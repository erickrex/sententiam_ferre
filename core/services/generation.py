"""
Generation job processor for BRIA image generation.

This module provides the GenerationJobProcessor class for managing
the lifecycle of image generation jobs.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.utils import timezone

from core.models import DecisionItem, GenerationJob
from core.services.bria import (
    BriaClient,
    BriaClientError,
    BriaRateLimitError,
    BriaServerError,
    GenerationStatus,
)
from core.services.prompt_builder import PromptBuilder, PromptBuilderError

logger = logging.getLogger(__name__)


class GenerationJobProcessorError(Exception):
    """Base exception for generation job processor errors."""
    pass


class GenerationJobProcessor:
    """
    Manages the lifecycle of BRIA image generation jobs.
    
    This processor handles:
    - Creating new generation jobs from character parameters
    - Polling the BRIA API for pending job status
    - Handling successful completions by updating items with image URLs
    - Handling failures by recording error messages
    """
    
    # Maximum number of concurrent jobs to process
    MAX_CONCURRENT_JOBS = 10
    
    # Maximum retry attempts for transient errors
    MAX_RETRIES = 3
    
    def __init__(
        self,
        bria_client: Optional[BriaClient] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ):
        """
        Initialize the generation job processor.
        
        Args:
            bria_client: Optional BriaClient instance. If not provided,
                        a new instance will be created.
            prompt_builder: Optional PromptBuilder instance. If not provided,
                           a new instance will be created.
        """
        self._bria_client = bria_client
        self._prompt_builder = prompt_builder or PromptBuilder()
    
    @property
    def bria_client(self) -> BriaClient:
        """Lazy initialization of BRIA client."""
        if self._bria_client is None:
            self._bria_client = BriaClient()
        return self._bria_client
    
    def create_job(
        self,
        item: DecisionItem,
        parameters: Dict[str, Any],
        enforce_locks: bool = True,
    ) -> GenerationJob:
        """
        Create and queue a new generation job.
        
        This method creates a GenerationJob record, builds the prompt from
        the provided parameters, and submits the request to the BRIA API.
        
        If the decision has locked parameters, they will be automatically
        applied to the generation. If the request tries to modify a locked
        parameter with a different value, an error will be raised.
        
        Args:
            item: The DecisionItem to associate with this generation.
            parameters: Generation parameters including:
                - description: Character description text
                - art_style: Art style (cartoon, pixel_art, etc.)
                - view_angle: View angle (side_profile, front_facing, etc.)
                - pose: Character pose (optional, default: idle)
                - expression: Facial expression (optional, default: neutral)
                - background: Background type (optional, default: transparent)
                - color_palette: Color palette (optional, default: vibrant)
            enforce_locks: Whether to enforce locked parameters from the decision.
                          Defaults to True.
        
        Returns:
            The created GenerationJob instance.
        
        Raises:
            GenerationJobProcessorError: If job creation fails or locked
                                        parameters are violated.
        """
        logger.info(f"Creating generation job for item {item.id}")
        
        # Get locked parameters from the decision
        decision = item.decision
        locked_params = decision.get_locked_params() if hasattr(decision, 'get_locked_params') else {}
        
        # Apply locked parameters and check for conflicts
        if enforce_locks and locked_params:
            parameters = self._apply_locked_params(parameters, locked_params)
        
        # Validate required parameters
        description = parameters.get("description")
        if not description:
            raise GenerationJobProcessorError("description is required")
        
        art_style = parameters.get("art_style")
        if not art_style:
            raise GenerationJobProcessorError("art_style is required")
        
        view_angle = parameters.get("view_angle")
        if not view_angle:
            raise GenerationJobProcessorError("view_angle is required")
        
        # Build the prompt
        try:
            prompt = self._prompt_builder.build_prompt(
                description=description,
                art_style=art_style,
                view_angle=view_angle,
                pose=parameters.get("pose", "idle"),
                expression=parameters.get("expression", "neutral"),
                background=parameters.get("background", "transparent"),
                color_palette=parameters.get("color_palette", "vibrant"),
            )
        except PromptBuilderError as e:
            raise GenerationJobProcessorError(f"Invalid parameters: {e}") from e
        
        # Create the job record
        with transaction.atomic():
            job = GenerationJob.objects.create(
                item=item,
                status="pending",
                parameters=parameters,
            )
            
            # Submit to BRIA FIBO API
            logger.info(f"Submitting prompt to BRIA FIBO: {prompt}")
            print(f"[GENERATION] Submitting prompt to BRIA: {prompt}")
            try:
                result = self.bria_client.generate(prompt=prompt, sync=False)
                
                # Check if BRIA returned a sync result (tuple with request_id, image_url, and fibo_json)
                if isinstance(result, tuple):
                    if len(result) == 3:
                        request_id, image_url, fibo_json = result
                    else:
                        request_id, image_url = result
                        fibo_json = None
                    
                    job.request_id = request_id
                    job.status = "completed"
                    job.image_url = image_url
                    job.completed_at = timezone.now()
                    
                    # Store FIBO JSON in job parameters
                    if fibo_json:
                        job_params = job.parameters or {}
                        job_params["fibo_json"] = fibo_json
                        job.parameters = job_params
                        logger.info(f"FIBO structured JSON saved to job {job.id}: {fibo_json}")
                    
                    job.save(update_fields=[
                        "request_id", "status", "image_url", "completed_at", "parameters", "updated_at"
                    ])
                    
                    # Update the item with the image URL and FIBO JSON
                    item_attributes = item.attributes or {}
                    item_attributes["image_url"] = image_url
                    item_attributes["generation_job_id"] = str(job.id)
                    if fibo_json:
                        item_attributes["fibo_json"] = fibo_json
                    item.attributes = item_attributes
                    item.save(update_fields=["attributes"])
                    
                    logger.info(
                        f"Generation job {job.id} completed synchronously via FIBO, "
                        f"image_url: {image_url[:50]}..."
                    )
                else:
                    # Async mode - store request_id for polling
                    request_id = result
                    job.request_id = request_id
                    job.status = "processing"
                    job.save(update_fields=["request_id", "status", "updated_at"])
                    
                    logger.info(
                        f"Generation job {job.id} submitted to BRIA, "
                        f"request_id: {request_id}"
                    )
                
            except BriaRateLimitError as e:
                # Keep as pending for retry later
                logger.warning(f"Rate limited creating job {job.id}: {e}")
                job.error_message = "Rate limited, will retry"
                job.save(update_fields=["error_message", "updated_at"])
                
            except BriaClientError as e:
                # Mark as failed
                logger.error(f"Failed to submit job {job.id}: {e}")
                job.status = "failed"
                
                # Check for content moderation error and provide helpful message
                error_str = str(e)
                if "content moderation" in error_str.lower() or "422" in error_str:
                    job.error_message = (
                        "Your description was flagged by content moderation. "
                        "Try using simpler, family-friendly terms. "
                        "Avoid words like 'attacking', 'angry', 'weapon', etc."
                    )
                else:
                    job.error_message = error_str
                
                job.save(update_fields=["status", "error_message", "updated_at"])
                raise GenerationJobProcessorError(f"Failed to submit job: {e}") from e
        
        return job
    
    def process_pending_jobs(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Poll and update all pending/processing jobs.
        
        This method queries for jobs that are pending or processing,
        checks their status with the BRIA API, and updates them accordingly.
        
        Args:
            limit: Maximum number of jobs to process. Defaults to MAX_CONCURRENT_JOBS.
        
        Returns:
            Dictionary with counts of processed jobs by outcome:
            - completed: Jobs that finished successfully
            - failed: Jobs that failed
            - still_processing: Jobs still in progress
            - errors: Jobs that encountered errors during polling
        """
        limit = limit or self.MAX_CONCURRENT_JOBS
        
        # Get jobs that need status checks
        jobs = GenerationJob.objects.filter(
            status__in=["pending", "processing"],
            request_id__isnull=False,
        ).order_by("created_at")[:limit]
        
        results = {
            "completed": 0,
            "failed": 0,
            "still_processing": 0,
            "errors": 0,
        }
        
        for job in jobs:
            try:
                self._process_single_job(job)
                
                # Refresh from DB to get updated status
                job.refresh_from_db()
                
                if job.status == "completed":
                    results["completed"] += 1
                elif job.status == "failed":
                    results["failed"] += 1
                else:
                    results["still_processing"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {e}")
                results["errors"] += 1
        
        # Also try to submit pending jobs without request_id
        pending_without_request = GenerationJob.objects.filter(
            status="pending",
            request_id__isnull=True,
        ).order_by("created_at")[:limit]
        
        for job in pending_without_request:
            try:
                self._submit_pending_job(job)
            except Exception as e:
                logger.error(f"Error submitting pending job {job.id}: {e}")
                results["errors"] += 1
        
        logger.info(f"Processed jobs: {results}")
        return results
    
    def _process_single_job(self, job: GenerationJob) -> None:
        """
        Process a single job by checking its status with BRIA FIBO.
        
        Args:
            job: The GenerationJob to process.
        """
        if not job.request_id:
            logger.warning(f"Job {job.id} has no request_id, skipping")
            return
        
        try:
            result = self.bria_client.check_status(job.request_id)
            
            if result.status == GenerationStatus.COMPLETED:
                self.handle_completion(job, result.image_url, result.fibo_json)
                
            elif result.status == GenerationStatus.FAILED:
                self.handle_failure(job, result.error_message or "Generation failed")
                
            elif result.status == GenerationStatus.PROCESSING:
                # Update status if it was pending
                if job.status == "pending":
                    job.status = "processing"
                    job.save(update_fields=["status", "updated_at"])
                    
        except BriaRateLimitError:
            logger.warning(f"Rate limited checking job {job.id}")
            # Don't update, will retry later
            
        except BriaServerError as e:
            logger.error(f"Server error checking job {job.id}: {e}")
            # Don't fail the job, will retry later
            
        except BriaClientError as e:
            logger.error(f"Error checking job {job.id}: {e}")
            self.handle_failure(job, str(e))
    
    def _submit_pending_job(self, job: GenerationJob) -> None:
        """
        Submit a pending job that doesn't have a request_id yet.
        
        Args:
            job: The GenerationJob to submit.
        """
        parameters = job.parameters
        description = parameters.get("description", "")
        
        try:
            prompt = self._prompt_builder.build_prompt(
                description=description,
                art_style=parameters.get("art_style", "cartoon"),
                view_angle=parameters.get("view_angle", "side_profile"),
                pose=parameters.get("pose", "idle"),
                expression=parameters.get("expression", "neutral"),
                background=parameters.get("background", "transparent"),
                color_palette=parameters.get("color_palette", "vibrant"),
            )
            
            result = self.bria_client.generate(prompt=prompt, sync=False)
            
            # Check if BRIA returned a sync result (tuple with request_id, image_url, and fibo_json)
            if isinstance(result, tuple):
                if len(result) == 3:
                    request_id, image_url, fibo_json = result
                else:
                    request_id, image_url = result
                    fibo_json = None
                job.request_id = request_id
                job.error_message = None
                job.save(update_fields=["request_id", "error_message", "updated_at"])
                self.handle_completion(job, image_url, fibo_json)
                logger.info(f"Pending job {job.id} completed synchronously via FIBO")
            else:
                request_id = result
                job.request_id = request_id
                job.status = "processing"
                job.error_message = None
                job.save(update_fields=["request_id", "status", "error_message", "updated_at"])
                logger.info(f"Submitted pending job {job.id} to FIBO, request_id: {request_id}")
            
        except BriaRateLimitError:
            logger.warning(f"Rate limited submitting job {job.id}")
            job.error_message = "Rate limited, will retry"
            job.save(update_fields=["error_message", "updated_at"])
            
        except (BriaClientError, PromptBuilderError) as e:
            logger.error(f"Failed to submit job {job.id}: {e}")
            self.handle_failure(job, str(e))
    
    def handle_completion(
        self,
        job: GenerationJob,
        image_url: Optional[str],
        fibo_json: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle successful generation completion.
        
        Updates the job status to completed and stores the image URL and FIBO JSON.
        Also updates the associated DecisionItem's attributes with the image URL and FIBO JSON.
        
        Args:
            job: The GenerationJob that completed.
            image_url: The URL of the generated image.
            fibo_json: The structured JSON inferred by FIBO (optional).
        """
        logger.info(f"Handling FIBO completion for job {job.id}, image_url: {image_url}")
        
        if fibo_json:
            logger.info(f"FIBO structured JSON for job {job.id}: {fibo_json}")
        
        with transaction.atomic():
            # Update job with FIBO JSON in parameters
            job.status = "completed"
            job.image_url = image_url
            job.completed_at = timezone.now()
            job.error_message = None
            
            if fibo_json:
                job_params = job.parameters or {}
                job_params["fibo_json"] = fibo_json
                job.parameters = job_params
            
            job.save(update_fields=[
                "status", "image_url", "completed_at", "error_message", "parameters", "updated_at"
            ])
            
            # Update the associated item's attributes with image_url and FIBO JSON
            item = job.item
            attributes = item.attributes or {}
            attributes["image_url"] = image_url
            attributes["generation_job_id"] = str(job.id)
            if fibo_json:
                attributes["fibo_json"] = fibo_json
            item.attributes = attributes
            item.save(update_fields=["attributes"])
            
            logger.info(
                f"Job {job.id} completed successfully via FIBO, "
                f"updated item {item.id} with image_url"
            )
    
    def handle_failure(
        self,
        job: GenerationJob,
        error_message: str,
    ) -> None:
        """
        Handle generation failure.
        
        Updates the job status to failed and records the error message.
        
        Args:
            job: The GenerationJob that failed.
            error_message: Description of the failure.
        """
        logger.error(f"Handling failure for job {job.id}: {error_message}")
        
        job.status = "failed"
        job.error_message = error_message
        job.save(update_fields=["status", "error_message", "updated_at"])
        
        logger.info(f"Job {job.id} marked as failed")
    
    def retry_job(self, job: GenerationJob) -> GenerationJob:
        """
        Retry a failed generation job.
        
        Creates a new job with the same parameters as the failed one.
        
        Args:
            job: The failed GenerationJob to retry.
        
        Returns:
            The new GenerationJob instance.
        
        Raises:
            GenerationJobProcessorError: If the job is not in failed status
                                        or retry fails.
        """
        if job.status != "failed":
            raise GenerationJobProcessorError(
                f"Can only retry failed jobs, current status: {job.status}"
            )
        
        logger.info(f"Retrying failed job {job.id}")
        
        return self.create_job(
            item=job.item,
            parameters=job.parameters,
        )
    
    def get_decision_generation_stats(self, decision_id: str) -> Dict[str, int]:
        """
        Get generation statistics for a decision.
        
        Args:
            decision_id: The UUID of the decision.
        
        Returns:
            Dictionary with counts by status:
            - pending: Jobs waiting to be processed
            - processing: Jobs currently being generated
            - completed: Successfully completed jobs
            - failed: Failed jobs
        """
        from django.db.models import Count
        
        stats = GenerationJob.objects.filter(
            item__decision_id=decision_id
        ).values("status").annotate(count=Count("id"))
        
        result = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }
        
        for stat in stats:
            if stat["status"] in result:
                result[stat["status"]] = stat["count"]
        
        return result
    
    def _apply_locked_params(
        self,
        parameters: Dict[str, Any],
        locked_params: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Apply locked parameters to the generation request.
        
        This method checks if any provided parameters conflict with locked
        parameters and raises an error if so. It also applies locked parameter
        values to the parameters dict.
        
        Args:
            parameters: The generation parameters from the request.
            locked_params: The locked parameters from the decision.
        
        Returns:
            Updated parameters dict with locked values applied.
        
        Raises:
            GenerationJobProcessorError: If a locked parameter is being
                                        modified with a different value.
        """
        # Create a copy to avoid modifying the original
        result = dict(parameters)
        
        for param_name, locked_value in locked_params.items():
            provided_value = parameters.get(param_name)
            
            if provided_value is not None and provided_value != locked_value:
                raise GenerationJobProcessorError(
                    f"Cannot modify locked parameter '{param_name}'. "
                    f"Locked value: '{locked_value}', provided value: '{provided_value}'"
                )
            
            # Apply the locked value
            result[param_name] = locked_value
        
        return result
    
    def validate_params_against_locks(
        self,
        decision,
        parameters: Dict[str, Any],
    ) -> List[str]:
        """
        Validate parameters against decision's locked parameters.
        
        This is a utility method that can be used to check parameters
        before creating a job, returning a list of validation errors.
        
        Args:
            decision: The Decision instance to check locks against.
            parameters: The generation parameters to validate.
        
        Returns:
            List of validation error messages. Empty if all valid.
        """
        errors = []
        locked_params = decision.get_locked_params() if hasattr(decision, 'get_locked_params') else {}
        
        for param_name, locked_value in locked_params.items():
            provided_value = parameters.get(param_name)
            
            if provided_value is not None and provided_value != locked_value:
                errors.append(
                    f"Parameter '{param_name}' is locked to '{locked_value}', "
                    f"cannot set to '{provided_value}'"
                )
        
        return errors
