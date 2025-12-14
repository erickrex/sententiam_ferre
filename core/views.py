from rest_framework import status, viewsets
from rest_framework.decorators import action, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q
from core.throttles import LoginRateThrottle
from core.models import (
    UserAccount, AppGroup, GroupMembership, Decision, Taxonomy, Term,
    DecisionItem, CatalogItem, DecisionItemTerm, DecisionVote, DecisionSelection,
    Question, AnswerOption, UserAnswer
)
from core.serializers import (
    UserAccountSerializer,
    UserRegistrationSerializer,
    UserLoginSerializer,
    AppGroupSerializer,
    AppGroupDetailSerializer,
    GroupMembershipSerializer,
    InviteUserSerializer,
    MembershipActionSerializer,
    DecisionSerializer,
    DecisionCreateSerializer,
    DecisionUpdateSerializer,
    TaxonomySerializer,
    TaxonomyDetailSerializer,
    TermSerializer,
    DecisionItemSerializer,
    DecisionItemCreateSerializer,
    DecisionItemUpdateSerializer,
    DecisionVoteSerializer,
    VoteSummarySerializer,
    DecisionSelectionSerializer,
    QuestionSerializer,
    UserAnswerSerializer,
    UserAnswerCreateSerializer
)


class AuthViewSet(viewsets.GenericViewSet):
    """ViewSet for authentication operations"""
    permission_classes = [AllowAny]
    serializer_class = UserAccountSerializer
    
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        """
        Create new user account
        POST /api/v1/auth/signup
        """
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Create authentication token
            token, created = Token.objects.get_or_create(user=user)
            
            # Return user data and token
            user_serializer = UserAccountSerializer(user)
            
            return Response({
                'status': 'success',
                'data': {
                    'user': user_serializer.data,
                    'token': token.key
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'message': 'Registration failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='login')
    @throttle_classes([LoginRateThrottle])
    def login(self, request):
        """
        Authenticate user and return token
        POST /api/v1/auth/login
        Rate limited to 5 attempts per 15 minutes
        """
        serializer = UserLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid credentials',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Get or create token
            token, created = Token.objects.get_or_create(user=user)
            
            # Return user data and token
            user_serializer = UserAccountSerializer(user)
            
            return Response({
                'status': 'success',
                'data': {
                    'user': user_serializer.data,
                    'token': token.key
                }
            }, status=status.HTTP_200_OK)
        
        # Return generic error to prevent user enumeration
        return Response({
            'status': 'error',
            'message': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current authenticated user
        GET /api/v1/auth/me
        """
        serializer = UserAccountSerializer(request.user)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        Invalidate user token
        POST /api/v1/auth/logout
        """
        try:
            # Delete the user's token
            request.user.auth_token.delete()
            
            return Response({
                'status': 'success',
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current user profile
        GET /api/v1/auth/me
        """
        serializer = UserAccountSerializer(request.user)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)



class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet for group CRUD operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = AppGroupSerializer
    
    def get_queryset(self):
        """Return groups where user is a confirmed member"""
        return AppGroup.objects.filter(
            memberships__user=self.request.user,
            memberships__is_confirmed=True
        ).distinct()
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return AppGroupDetailSerializer
        return AppGroupSerializer
    
    def create(self, request):
        """
        Create a new group
        POST /api/v1/groups
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            group = serializer.save()
            
            return Response({
                'status': 'success',
                'data': AppGroupDetailSerializer(group).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'status': 'error',
            'message': 'Group creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """
        Get group details
        GET /api/v1/groups/:id
        """
        try:
            group = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(group)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def list(self, request):
        """
        List user's groups
        GET /api/v1/groups
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get', 'post'], url_path='members')
    def members(self, request, pk=None):
        """
        List group members (GET) or invite user to group (POST)
        GET /api/v1/groups/:id/members
        POST /api/v1/groups/:id/members
        """
        if request.method == 'GET':
            # List members
            try:
                group = self.get_queryset().get(pk=pk)
                memberships = group.memberships.all()
                serializer = GroupMembershipSerializer(memberships, many=True)
                
                return Response({
                    'status': 'success',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except AppGroup.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Group not found or access denied'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # POST - Invite member
        try:
            group = self.get_queryset().get(pk=pk)
            
            # Check if user is admin
            membership = group.memberships.get(user=request.user, is_confirmed=True)
            if membership.role != 'admin':
                return Response({
                    'status': 'error',
                    'message': 'Only admins can invite members'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = InviteUserSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid invitation data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find the user to invite
            user_to_invite = None
            if serializer.validated_data.get('user_id'):
                try:
                    user_to_invite = UserAccount.objects.get(id=serializer.validated_data['user_id'])
                except UserAccount.DoesNotExist:
                    pass
            elif serializer.validated_data.get('username'):
                try:
                    user_to_invite = UserAccount.objects.get(username=serializer.validated_data['username'])
                except UserAccount.DoesNotExist:
                    pass
            elif serializer.validated_data.get('email'):
                try:
                    user_to_invite = UserAccount.objects.get(email=serializer.validated_data['email'])
                except UserAccount.DoesNotExist:
                    pass
            
            if not user_to_invite:
                return Response({
                    'status': 'error',
                    'message': 'User not found. Please ensure the user is registered.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is already a member
            existing_membership = GroupMembership.objects.filter(
                group=group,
                user=user_to_invite
            ).first()
            
            if existing_membership:
                if existing_membership.is_confirmed:
                    return Response({
                        'status': 'error',
                        'message': 'User is already a member of this group'
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({
                        'status': 'error',
                        'message': 'User already has a pending invitation'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create invitation
            new_membership = GroupMembership.objects.create(
                group=group,
                user=user_to_invite,
                role=serializer.validated_data.get('role', 'member'),
                membership_type='invitation',
                status='pending',
                is_confirmed=False
            )
            
            membership_serializer = GroupMembershipSerializer(new_membership)
            
            return Response({
                'status': 'success',
                'data': membership_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        except GroupMembership.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You are not a member of this group'
            }, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['patch', 'delete'], url_path='members/(?P<user_id>[^/.]+)')
    def manage_member(self, request, pk=None, user_id=None):
        """
        Manage group membership
        PATCH /api/v1/groups/:id/members/:userId - Accept or decline invitation
        DELETE /api/v1/groups/:id/members/:userId - Remove member from group
        """
        try:
            group = AppGroup.objects.get(pk=pk)
            
            # Get the membership
            membership = GroupMembership.objects.filter(
                group=group,
                user__id=user_id
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'Membership not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            if request.method == 'PATCH':
                # Accept or decline invitation
                serializer = MembershipActionSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({
                        'status': 'error',
                        'message': 'Invalid action',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                action_type = serializer.validated_data['action']
                
                # Only the invited user can accept/decline their own invitation
                if str(request.user.id) != str(user_id):
                    return Response({
                        'status': 'error',
                        'message': 'You can only manage your own invitations'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                if membership.is_confirmed:
                    return Response({
                        'status': 'error',
                        'message': 'Invitation already accepted'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if action_type == 'accept':
                    # Accept invitation
                    membership.is_confirmed = True
                    membership.confirmed_at = timezone.now()
                    membership.save()
                    
                    membership_serializer = GroupMembershipSerializer(membership)
                    
                    return Response({
                        'status': 'success',
                        'data': membership_serializer.data
                    }, status=status.HTTP_200_OK)
                
                elif action_type == 'decline':
                    # Decline invitation - delete membership
                    membership.delete()
                    
                    return Response({
                        'status': 'success',
                        'message': 'Invitation declined'
                    }, status=status.HTTP_200_OK)
            
            elif request.method == 'DELETE':
                # Remove member from group
                # Check if requester is a confirmed member
                try:
                    requester_membership = group.memberships.get(user=request.user, is_confirmed=True)
                except GroupMembership.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'You are not a member of this group'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Check if requester is admin
                if requester_membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can remove members'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Prevent removing the group creator if they're the last admin
                if membership.user == group.created_by:
                    admin_count = group.memberships.filter(role='admin', is_confirmed=True).count()
                    if admin_count <= 1:
                        return Response({
                            'status': 'error',
                            'message': 'Cannot remove the last admin from the group'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                membership.delete()
                
                return Response({
                    'status': 'success',
                    'message': 'Member removed successfully'
                }, status=status.HTTP_200_OK)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='decisions')
    def list_decisions(self, request, pk=None):
        """
        List group decisions
        GET /api/v1/groups/:id/decisions
        """
        try:
            group = self.get_queryset().get(pk=pk)
            decisions = Decision.objects.filter(group=group)
            
            from core.serializers import DecisionSerializer
            serializer = DecisionSerializer(decisions, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], url_path='join-request')
    def join_request(self, request):
        """
        Create a join request for a group
        POST /api/v1/groups/join-request/
        
        Body:
        {
            "group_name": "string"
        }
        """
        from core.serializers import JoinRequestSerializer
        
        serializer = JoinRequestSerializer(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Join request failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the group from the serializer (it was validated and stored there)
        group = serializer.group
        
        # Create the join request
        membership = GroupMembership.objects.create(
            group=group,
            user=request.user,
            role='member',
            membership_type='request',
            status='pending',
            is_confirmed=False
        )
        
        membership_serializer = GroupMembershipSerializer(membership)
        
        return Response({
            'status': 'success',
            'message': 'Join request sent successfully',
            'data': membership_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """
        List current user's join requests
        GET /api/v1/groups/my-requests/
        
        Returns pending and rejected requests, sorted by status (pending first) then date
        """
        # Get all join requests for the current user
        requests = GroupMembership.objects.filter(
            user=request.user,
            membership_type='request'
        ).filter(
            Q(status='pending') | Q(status='rejected')
        ).select_related('group').order_by(
            # Sort by status (pending first), then by date descending
            '-status',  # 'pending' comes after 'rejected' alphabetically, so we reverse
            '-invited_at'
        )
        
        # Custom sort to ensure pending comes first
        pending_requests = requests.filter(status='pending').order_by('-invited_at')
        rejected_requests = requests.filter(status='rejected').order_by('-invited_at')
        
        # Combine the querysets
        all_requests = list(pending_requests) + list(rejected_requests)
        
        serializer = GroupMembershipSerializer(all_requests, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['patch'], url_path='my-requests/(?P<request_id>[^/.]+)')
    def manage_my_request(self, request, request_id=None):
        """
        Manage own join request (resend or delete)
        PATCH /api/v1/groups/my-requests/:id/
        
        Body:
        {
            "action": "resend" | "delete"
        }
        """
        try:
            # Get the membership
            membership = GroupMembership.objects.get(
                id=request_id,
                user=request.user,
                membership_type='request'
            )
            
            # Validate action
            serializer = MembershipActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid action',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            if action == 'resend':
                # Can only resend rejected requests
                if membership.status != 'rejected':
                    return Response({
                        'status': 'error',
                        'message': 'Can only resend rejected requests'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to pending
                membership.status = 'pending'
                membership.invited_at = timezone.now()
                membership.rejected_at = None
                membership.save()
                
                membership_serializer = GroupMembershipSerializer(membership)
                
                return Response({
                    'status': 'success',
                    'message': 'Request resent',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            elif action == 'delete':
                # Can only delete rejected requests
                if membership.status != 'rejected':
                    return Response({
                        'status': 'error',
                        'message': 'Can only delete rejected requests'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Delete the membership
                membership.delete()
                
                return Response({
                    'status': 'success',
                    'message': 'Record deleted successfully'
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': f'Invalid action: {action}. Use "resend" or "delete"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except GroupMembership.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Request not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='my-invitations')
    def my_invitations(self, request):
        """
        List current user's invitations
        GET /api/v1/groups/my-invitations/
        
        Returns pending and rejected invitations
        """
        # Get all invitations for the current user
        invitations = GroupMembership.objects.filter(
            user=request.user,
            membership_type='invitation'
        ).filter(
            Q(status='pending') | Q(status='rejected')
        ).select_related('group').order_by(
            '-invited_at'
        )
        
        # Custom sort to ensure pending comes first
        pending_invitations = invitations.filter(status='pending').order_by('-invited_at')
        rejected_invitations = invitations.filter(status='rejected').order_by('-invited_at')
        
        # Combine the querysets
        all_invitations = list(pending_invitations) + list(rejected_invitations)
        
        serializer = GroupMembershipSerializer(all_invitations, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['patch'], url_path='my-invitations/(?P<invitation_id>[^/.]+)')
    def manage_my_invitation(self, request, invitation_id=None):
        """
        Manage received invitation (accept or reject)
        PATCH /api/v1/groups/my-invitations/:id/
        
        Body:
        {
            "action": "accept" | "reject"
        }
        """
        try:
            # Get the membership
            membership = GroupMembership.objects.get(
                id=invitation_id,
                user=request.user,
                membership_type='invitation'
            )
            
            # Validate action
            serializer = MembershipActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid action',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            if action == 'accept':
                # Can only accept pending invitations
                if membership.status != 'pending':
                    return Response({
                        'status': 'error',
                        'message': 'Can only accept pending invitations'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to confirmed
                membership.status = 'confirmed'
                membership.is_confirmed = True
                membership.confirmed_at = timezone.now()
                membership.save()
                
                membership_serializer = GroupMembershipSerializer(membership)
                
                return Response({
                    'status': 'success',
                    'message': 'Invitation accepted',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            elif action == 'reject':
                # Can only reject pending invitations
                if membership.status != 'pending':
                    return Response({
                        'status': 'error',
                        'message': 'Can only reject pending invitations'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to rejected
                membership.status = 'rejected'
                membership.rejected_at = timezone.now()
                membership.save()
                
                membership_serializer = GroupMembershipSerializer(membership)
                
                return Response({
                    'status': 'success',
                    'message': 'Invitation declined',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': f'Invalid action: {action}. Use "accept" or "reject"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except GroupMembership.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Invitation not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='join-requests')
    def list_join_requests(self, request, pk=None):
        """
        List pending join requests for a group (admin only)
        GET /api/v1/groups/:id/join-requests/
        
        Returns pending join requests with count
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can view join requests'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all pending join requests for this group
            join_requests = GroupMembership.objects.filter(
                group=group,
                membership_type='request',
                status='pending'
            ).select_related('user').order_by('-invited_at')
            
            serializer = GroupMembershipSerializer(join_requests, many=True)
            
            return Response({
                'status': 'success',
                'data': {
                    'results': serializer.data,
                    'count': join_requests.count()
                }
            }, status=status.HTTP_200_OK)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['patch'], url_path='join-requests/(?P<request_id>[^/.]+)')
    def manage_join_request(self, request, pk=None, request_id=None):
        """
        Manage a join request (approve or reject) - admin only
        PATCH /api/v1/groups/:id/join-requests/:requestId/
        
        Body:
        {
            "action": "approve" | "reject"
        }
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                admin_membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if admin_membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can manage join requests'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the join request
            try:
                join_request = GroupMembership.objects.get(
                    id=request_id,
                    group=group,
                    membership_type='request'
                )
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Join request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate action
            serializer = MembershipActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid action',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            if action == 'approve':
                # Can only approve pending requests
                if join_request.status != 'pending':
                    return Response({
                        'status': 'error',
                        'message': 'Can only approve pending requests'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to confirmed
                join_request.status = 'confirmed'
                join_request.is_confirmed = True
                join_request.confirmed_at = timezone.now()
                join_request.save()
                
                membership_serializer = GroupMembershipSerializer(join_request)
                
                return Response({
                    'status': 'success',
                    'message': 'Request approved',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            elif action == 'reject':
                # Can only reject pending requests
                if join_request.status != 'pending':
                    return Response({
                        'status': 'error',
                        'message': 'Can only reject pending requests'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to rejected
                join_request.status = 'rejected'
                join_request.rejected_at = timezone.now()
                join_request.save()
                
                membership_serializer = GroupMembershipSerializer(join_request)
                
                return Response({
                    'status': 'success',
                    'message': 'Request rejected',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': f'Invalid action: {action}. Use "approve" or "reject"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='rejected-invitations')
    def list_rejected_invitations(self, request, pk=None):
        """
        List rejected invitations for a group (admin only)
        GET /api/v1/groups/:id/rejected-invitations/
        
        Returns rejected invitations
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can view rejected invitations'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all rejected invitations for this group
            rejected_invitations = GroupMembership.objects.filter(
                group=group,
                membership_type='invitation',
                status='rejected'
            ).select_related('user').order_by('-rejected_at')
            
            serializer = GroupMembershipSerializer(rejected_invitations, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['patch'], url_path='rejected-invitations/(?P<invitation_id>[^/.]+)')
    def manage_rejected_invitation(self, request, pk=None, invitation_id=None):
        """
        Manage a rejected invitation (resend or delete) - admin only
        PATCH /api/v1/groups/:id/rejected-invitations/:id/
        
        Body:
        {
            "action": "resend" | "delete"
        }
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                admin_membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if admin_membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can manage rejected invitations'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the rejected invitation
            try:
                invitation = GroupMembership.objects.get(
                    id=invitation_id,
                    group=group,
                    membership_type='invitation'
                )
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Invitation not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate action
            serializer = MembershipActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid action',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            if action == 'resend':
                # Can only resend rejected invitations
                if invitation.status != 'rejected':
                    return Response({
                        'status': 'error',
                        'message': 'Can only resend rejected invitations'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update status to pending
                invitation.status = 'pending'
                invitation.invited_at = timezone.now()
                invitation.rejected_at = None
                invitation.save()
                
                membership_serializer = GroupMembershipSerializer(invitation)
                
                return Response({
                    'status': 'success',
                    'message': 'Invitation resent',
                    'data': membership_serializer.data
                }, status=status.HTTP_200_OK)
            
            elif action == 'delete':
                # Can only delete rejected invitations
                if invitation.status != 'rejected':
                    return Response({
                        'status': 'error',
                        'message': 'Can only delete rejected invitations'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Delete the invitation
                invitation.delete()
                
                return Response({
                    'status': 'success',
                    'message': 'Record deleted successfully'
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': f'Invalid action: {action}. Use "resend" or "delete"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='rejected-requests')
    def list_rejected_requests(self, request, pk=None):
        """
        List rejected join requests for a group (admin only)
        GET /api/v1/groups/:id/rejected-requests/
        
        Returns rejected join requests
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can view rejected requests'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all rejected join requests for this group
            rejected_requests = GroupMembership.objects.filter(
                group=group,
                membership_type='request',
                status='rejected'
            ).select_related('user').order_by('-rejected_at')
            
            serializer = GroupMembershipSerializer(rejected_requests, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['patch'], url_path='rejected-requests/(?P<request_id>[^/.]+)')
    def manage_rejected_request(self, request, pk=None, request_id=None):
        """
        Manage a rejected join request (delete only) - admin only
        PATCH /api/v1/groups/:id/rejected-requests/:id/
        
        Body:
        {
            "action": "delete"
        }
        """
        try:
            # Get the group
            group = AppGroup.objects.get(pk=pk)
            
            # Check if user is an admin of this group
            try:
                admin_membership = GroupMembership.objects.get(
                    group=group,
                    user=request.user,
                    is_confirmed=True
                )
                if admin_membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can manage rejected requests'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the rejected request
            try:
                rejected_request = GroupMembership.objects.get(
                    id=request_id,
                    group=group,
                    membership_type='request'
                )
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Request not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Validate action
            serializer = MembershipActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Invalid action',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            if action == 'delete':
                # Can only delete rejected requests
                if rejected_request.status != 'rejected':
                    return Response({
                        'status': 'error',
                        'message': 'Can only delete rejected requests'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Delete the request
                rejected_request.delete()
                
                return Response({
                    'status': 'success',
                    'message': 'Record deleted successfully'
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'status': 'error',
                    'message': f'Invalid action: {action}. Only "delete" is allowed for rejected requests'
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except AppGroup.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)



class DecisionViewSet(viewsets.ModelViewSet):
    """ViewSet for decision CRUD operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = DecisionSerializer
    
    def get_queryset(self):
        """Return decisions where user is a confirmed member of the owning group or a shared group"""
        from core.models import DecisionSharedGroup
        
        # Get decisions from groups user is a confirmed member of
        owned_decisions = Q(
            group__memberships__user=self.request.user,
            group__memberships__is_confirmed=True
        )
        
        # Get decisions shared with groups user is a confirmed member of
        shared_decisions = Q(
            shared_groups__group__memberships__user=self.request.user,
            shared_groups__group__memberships__is_confirmed=True
        )
        
        return Decision.objects.filter(owned_decisions | shared_decisions).distinct()
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'create':
            return DecisionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DecisionUpdateSerializer
        return DecisionSerializer
    
    def create(self, request):
        """
        Create a new decision
        POST /api/v1/decisions
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Decision creation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user is a confirmed member of the group
        group_id = serializer.validated_data['group'].id
        try:
            membership = GroupMembership.objects.get(
                group_id=group_id,
                user=request.user,
                is_confirmed=True
            )
        except GroupMembership.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'You must be a confirmed member of the group to create decisions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Create the decision
        decision = serializer.save()
        
        # Return with full serializer
        response_serializer = DecisionSerializer(decision)
        
        return Response({
            'status': 'success',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """
        Get decision details
        GET /api/v1/decisions/:id
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(decision)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        """
        Update decision
        PATCH /api/v1/decisions/:id
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Check if user is admin
            try:
                membership = GroupMembership.objects.get(
                    group=decision.group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can update decisions'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(decision, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Decision update failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            
            # Return with full serializer
            response_serializer = DecisionSerializer(decision)
            
            return Response({
                'status': 'success',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def partial_update(self, request, pk=None):
        """
        Partial update decision
        PATCH /api/v1/decisions/:id
        """
        return self.update(request, pk)
    
    def list(self, request):
        """
        List user's decisions (all decisions from groups they're in)
        GET /api/v1/decisions
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='share-group')
    def share_group(self, request, pk=None):
        """
        Share decision with another group
        POST /api/v1/decisions/:id/share-group
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Check if user is admin of the owning group
            try:
                membership = GroupMembership.objects.get(
                    group=decision.group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can share decisions'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the target group ID
            target_group_id = request.data.get('group_id')
            if not target_group_id:
                return Response({
                    'status': 'error',
                    'message': 'group_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify target group exists
            try:
                target_group = AppGroup.objects.get(id=target_group_id)
            except AppGroup.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Target group not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if already shared
            from core.models import DecisionSharedGroup
            if DecisionSharedGroup.objects.filter(decision=decision, group=target_group).exists():
                return Response({
                    'status': 'error',
                    'message': 'Decision is already shared with this group'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create the share
            shared = DecisionSharedGroup.objects.create(
                decision=decision,
                group=target_group
            )
            
            from core.serializers import DecisionSharedGroupSerializer
            serializer = DecisionSharedGroupSerializer(shared)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='favourites')
    def list_favourites(self, request, pk=None):
        """
        List favourites (items that met approval rules) for a decision
        GET /api/v1/decisions/:id/favourites
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Get all favourites for this decision
            favourites = DecisionSelection.objects.filter(
                decision=decision
            ).select_related('item', 'decision').prefetch_related('item__item_terms__term__taxonomy')
            
            serializer = DecisionSelectionSerializer(favourites, many=True)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get', 'post'], url_path='items')
    def items(self, request, pk=None):
        """
        List or create items for a decision
        GET /api/v1/decisions/:id/items/
        POST /api/v1/decisions/:id/items/
        """
        try:
            decision = self.get_queryset().get(pk=pk)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            # List items for this decision
            items = DecisionItem.objects.filter(decision=decision).select_related(
                'decision', 'catalog_item'
            ).prefetch_related('item_terms__term__taxonomy')
            
            # Apply tag filters
            tag_ids = request.query_params.getlist('tag')
            if tag_ids:
                for tag_id in tag_ids:
                    items = items.filter(item_terms__term_id=tag_id)
            
            # Apply JSONB attribute filters
            known_params = {'tag', 'page', 'page_size'}
            attribute_filters = {
                key: value 
                for key, value in request.query_params.items() 
                if key not in known_params
            }
            
            for attr_key, attr_value in attribute_filters.items():
                try:
                    attr_value = int(attr_value)
                except ValueError:
                    try:
                        attr_value = float(attr_value)
                    except ValueError:
                        if attr_value.lower() in ('true', 'false'):
                            attr_value = attr_value.lower() == 'true'
                
                items = items.filter(attributes__contains={attr_key: attr_value})
            
            # Get pagination parameters
            try:
                page = int(request.query_params.get('page', 1))
                page_size = int(request.query_params.get('page_size', 20))
                page_size = min(page_size, 100)
                if page < 1:
                    page = 1
                if page_size < 1:
                    page_size = 20
            except ValueError:
                return Response({
                    'status': 'error',
                    'message': 'Invalid page or page_size parameter'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get total count
            total_count = items.count()
            
            # Calculate pagination
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # Get paginated items
            paginated_items = items[start_index:end_index]
            
            # Serialize
            serializer = DecisionItemSerializer(paginated_items, many=True)
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            return Response({
                'status': 'success',
                'data': {
                    'results': serializer.data,
                    'count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_previous': has_previous
                }
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Create item for this decision
            # Check if user is a confirmed member
            membership = GroupMembership.objects.filter(
                group=decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to add items to this decision'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Add decision to the data
            data = request.data.copy()
            data['decision'] = str(decision.id)
            
            serializer = DecisionItemCreateSerializer(data=data)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Item creation failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            item = serializer.save()
            
            return Response({
                'status': 'success',
                'data': DecisionItemSerializer(item).data
            }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='lock-parameter')
    def lock_parameter(self, request, pk=None):
        """
        Lock a parameter for a decision (admin only)
        POST /api/v1/decisions/:id/lock-parameter/
        
        Body:
        {
            "parameter": "art_style",
            "value": "cartoon"
        }
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Check if user is admin of the decision's group
            try:
                membership = GroupMembership.objects.get(
                    group=decision.group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can lock parameters'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate request data
            parameter = request.data.get('parameter')
            value = request.data.get('value')
            
            if not parameter:
                return Response({
                    'status': 'error',
                    'message': 'parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not value:
                return Response({
                    'status': 'error',
                    'message': 'value is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate parameter name
            if parameter not in Decision.LOCKABLE_PARAMS:
                return Response({
                    'status': 'error',
                    'message': f"Invalid parameter: '{parameter}'. "
                              f"Valid parameters: {', '.join(Decision.LOCKABLE_PARAMS)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate parameter value
            valid_values = Decision.VALID_PARAM_VALUES.get(parameter, [])
            if value not in valid_values:
                return Response({
                    'status': 'error',
                    'message': f"Invalid value '{value}' for parameter '{parameter}'. "
                              f"Valid values: {', '.join(valid_values)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update the rules with the locked parameter
            rules = decision.rules or {}
            locked_params = rules.get('locked_params', {})
            locked_params[parameter] = value
            rules['locked_params'] = locked_params
            decision.rules = rules
            decision.save(update_fields=['rules', 'updated_at'])
            
            serializer = DecisionSerializer(decision)
            
            return Response({
                'status': 'success',
                'message': f"Parameter '{parameter}' locked to '{value}'",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='unlock-parameter')
    def unlock_parameter(self, request, pk=None):
        """
        Unlock a parameter for a decision (admin only)
        POST /api/v1/decisions/:id/unlock-parameter/
        
        Body:
        {
            "parameter": "art_style"
        }
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Check if user is admin of the decision's group
            try:
                membership = GroupMembership.objects.get(
                    group=decision.group,
                    user=request.user,
                    is_confirmed=True
                )
                if membership.role != 'admin':
                    return Response({
                        'status': 'error',
                        'message': 'Only admins can unlock parameters'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupMembership.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'You are not a member of this group'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Validate request data
            parameter = request.data.get('parameter')
            
            if not parameter:
                return Response({
                    'status': 'error',
                    'message': 'parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate parameter name
            if parameter not in Decision.LOCKABLE_PARAMS:
                return Response({
                    'status': 'error',
                    'message': f"Invalid parameter: '{parameter}'. "
                              f"Valid parameters: {', '.join(Decision.LOCKABLE_PARAMS)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if parameter is actually locked
            rules = decision.rules or {}
            locked_params = rules.get('locked_params', {})
            
            if parameter not in locked_params:
                return Response({
                    'status': 'error',
                    'message': f"Parameter '{parameter}' is not locked"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove the locked parameter
            del locked_params[parameter]
            
            # Clean up empty locked_params dict
            if locked_params:
                rules['locked_params'] = locked_params
            elif 'locked_params' in rules:
                del rules['locked_params']
            
            decision.rules = rules
            decision.save(update_fields=['rules', 'updated_at'])
            
            serializer = DecisionSerializer(decision)
            
            return Response({
                'status': 'success',
                'message': f"Parameter '{parameter}' unlocked",
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='locked-params')
    def get_locked_params(self, request, pk=None):
        """
        Get locked parameters for a decision
        GET /api/v1/decisions/:id/locked-params/
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            locked_params = decision.get_locked_params()
            
            return Response({
                'status': 'success',
                'data': {
                    'locked_params': locked_params,
                    'lockable_params': Decision.LOCKABLE_PARAMS,
                    'valid_values': Decision.VALID_PARAM_VALUES
                }
            }, status=status.HTTP_200_OK)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)



class TaxonomyViewSet(viewsets.ModelViewSet):
    """ViewSet for taxonomy CRUD operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = TaxonomySerializer
    queryset = Taxonomy.objects.all()
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return TaxonomyDetailSerializer
        return TaxonomySerializer
    
    def list(self, request):
        """
        List all taxonomies
        GET /api/v1/taxonomies
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        """
        Create a new taxonomy
        POST /api/v1/taxonomies
        """
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Taxonomy creation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        taxonomy = serializer.save()
        
        return Response({
            'status': 'success',
            'data': TaxonomyDetailSerializer(taxonomy).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """
        Get taxonomy details with terms
        GET /api/v1/taxonomies/:id
        """
        try:
            taxonomy = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(taxonomy)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Taxonomy.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Taxonomy not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get', 'post'], url_path='terms')
    def terms(self, request, pk=None):
        """
        List all terms in a taxonomy (GET) or add a term (POST)
        GET /api/v1/taxonomies/:id/terms
        POST /api/v1/taxonomies/:id/terms
        """
        try:
            taxonomy = self.get_queryset().get(pk=pk)
            
            if request.method == 'GET':
                # List terms
                terms = taxonomy.terms.all()
                serializer = TermSerializer(terms, many=True)
                
                return Response({
                    'status': 'success',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            
            elif request.method == 'POST':
                # Add a term
                # Add taxonomy to the request data
                data = request.data.copy()
                data['taxonomy'] = taxonomy.id
                
                serializer = TermSerializer(data=data)
                
                if not serializer.is_valid():
                    return Response({
                        'status': 'error',
                        'message': 'Term creation failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                term = serializer.save()
                
                return Response({
                    'status': 'success',
                    'data': TermSerializer(term).data
                }, status=status.HTTP_201_CREATED)
            
        except Taxonomy.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Taxonomy not found'
            }, status=status.HTTP_404_NOT_FOUND)



class DecisionItemViewSet(viewsets.ModelViewSet):
    """ViewSet for decision item CRUD operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = DecisionItemSerializer
    queryset = DecisionItem.objects.all()
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'create':
            return DecisionItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DecisionItemUpdateSerializer
        return DecisionItemSerializer
    
    def get_queryset(self):
        """Filter items based on user's group membership"""
        user = self.request.user
        
        # Get all groups where user is a confirmed member
        user_groups = AppGroup.objects.filter(
            memberships__user=user,
            memberships__is_confirmed=True
        )
        
        # Return items from decisions in those groups
        return DecisionItem.objects.filter(
            decision__group__in=user_groups
        ).select_related('decision', 'catalog_item').prefetch_related('item_terms__term__taxonomy')
    
    def list(self, request):
        """
        List items for a decision with filtering and pagination
        GET /api/v1/decisions/:decision_id/items
        
        Query parameters:
        - decision_id: Required. The decision to list items for
        - tag: Optional. Filter by term ID (can be repeated for multiple tags)
        - page: Optional. Page number (default: 1)
        - page_size: Optional. Items per page (default: 20, max: 100)
        - Any JSONB attribute key: Optional. Filter by attribute value
        """
        decision_id = request.query_params.get('decision_id')
        
        if not decision_id:
            return Response({
                'status': 'error',
                'message': 'decision_id query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user has access to this decision
        try:
            decision = Decision.objects.get(pk=decision_id)
            
            # Check if user is a confirmed member of the decision's group
            is_member = GroupMembership.objects.filter(
                group=decision.group,
                user=request.user,
                is_confirmed=True
            ).exists()
            
            if not is_member:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to access this decision'
                }, status=status.HTTP_403_FORBIDDEN)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Start with items for this decision
        items = self.get_queryset().filter(decision_id=decision_id)
        
        # Apply tag filters
        tag_ids = request.query_params.getlist('tag')
        if tag_ids:
            # Filter items that have ALL specified tags
            for tag_id in tag_ids:
                items = items.filter(item_terms__term_id=tag_id)
        
        # Apply JSONB attribute filters
        # Get all query params except known ones
        known_params = {'decision_id', 'tag', 'page', 'page_size'}
        attribute_filters = {
            key: value 
            for key, value in request.query_params.items() 
            if key not in known_params
        }
        
        # Apply each attribute filter
        for attr_key, attr_value in attribute_filters.items():
            # Try to convert value to appropriate type
            try:
                # Try integer
                attr_value = int(attr_value)
            except ValueError:
                try:
                    # Try float
                    attr_value = float(attr_value)
                except ValueError:
                    # Try boolean
                    if attr_value.lower() in ('true', 'false'):
                        attr_value = attr_value.lower() == 'true'
                    # Otherwise keep as string
            
            # Filter using JSONB containment
            items = items.filter(attributes__contains={attr_key: attr_value})
        
        # Get pagination parameters
        try:
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # Limit page_size to max 100
            page_size = min(page_size, 100)
            
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
                
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid page or page_size parameter'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get total count
        total_count = items.count()
        
        # Calculate pagination
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        # Get paginated items
        paginated_items = items[start_index:end_index]
        
        # Serialize
        serializer = self.get_serializer(paginated_items, many=True)
        
        # Calculate pagination metadata
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return Response({
            'status': 'success',
            'data': {
                'results': serializer.data,
                'count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_previous': has_previous
            }
        }, status=status.HTTP_200_OK)
    
    def create(self, request):
        """
        Add item to a decision
        POST /api/v1/decisions/:decision_id/items
        """
        decision_id = request.data.get('decision')
        
        if not decision_id:
            return Response({
                'status': 'error',
                'message': 'decision field is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify user has access to this decision
        try:
            decision = Decision.objects.get(pk=decision_id)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to add items to this decision'
                }, status=status.HTTP_403_FORBIDDEN)
            
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create the item
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Item creation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        item = serializer.save()
        
        return Response({
            'status': 'success',
            'data': DecisionItemSerializer(item).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """
        Get item details
        GET /api/v1/items/:id
        """
        try:
            item = self.get_queryset().get(pk=pk)
            serializer = self.get_serializer(item)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        """
        Update item
        PATCH /api/v1/items/:id
        """
        try:
            item = self.get_queryset().get(pk=pk)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to update this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = self.get_serializer(item, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'status': 'error',
                    'message': 'Item update failed',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            item = serializer.save()
            
            return Response({
                'status': 'success',
                'data': DecisionItemSerializer(item).data
            }, status=status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def partial_update(self, request, pk=None):
        """
        Partial update item
        PATCH /api/v1/items/:id
        """
        return self.update(request, pk)
    
    def destroy(self, request, pk=None):
        """
        Delete item
        DELETE /api/v1/items/:id
        """
        try:
            item = self.get_queryset().get(pk=pk)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to delete this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            item.delete()
            
            return Response({
                'status': 'success',
                'message': 'Item deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='terms/(?P<term_id>[^/.]+)')
    def tag_item(self, request, pk=None, term_id=None):
        """
        Tag an item with a term
        POST /api/v1/items/:id/terms/:termId
        """
        try:
            item = self.get_queryset().get(pk=pk)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to tag this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the term
            try:
                term = Term.objects.get(pk=term_id)
            except Term.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Term not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create the tag (or get if already exists)
            item_term, created = DecisionItemTerm.objects.get_or_create(
                item=item,
                term=term
            )
            
            if created:
                message = 'Item tagged successfully'
            else:
                message = 'Item already has this tag'
            
            return Response({
                'status': 'success',
                'message': message,
                'data': {
                    'item_id': str(item.id),
                    'term_id': str(term.id),
                    'term_value': term.value,
                    'taxonomy_name': term.taxonomy.name
                }
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], url_path='terms/(?P<term_id>[^/.]+)')
    def untag_item(self, request, pk=None, term_id=None):
        """
        Remove a tag from an item
        DELETE /api/v1/items/:id/terms/:termId
        """
        try:
            item = self.get_queryset().get(pk=pk)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to untag this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the term
            try:
                term = Term.objects.get(pk=term_id)
            except Term.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Term not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Delete the tag
            deleted_count, _ = DecisionItemTerm.objects.filter(
                item=item,
                term=term
            ).delete()
            
            if deleted_count > 0:
                message = 'Tag removed successfully'
            else:
                message = 'Item does not have this tag'
            
            return Response({
                'status': 'success',
                'message': message
            }, status=status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)



class VoteViewSet(viewsets.GenericViewSet):
    """ViewSet for voting operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = DecisionVoteSerializer
    
    def get_queryset(self):
        """Filter votes based on user's group membership"""
        user = self.request.user
        
        # Get all groups where user is a confirmed member
        user_groups = AppGroup.objects.filter(
            memberships__user=user,
            memberships__is_confirmed=True
        )
        
        # Return votes from items in decisions in those groups
        return DecisionVote.objects.filter(
            item__decision__group__in=user_groups
        ).select_related('item', 'user')
    
    @action(detail=False, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/votes')
    def cast_vote(self, request, item_id=None):
        """
        Cast or update a vote on an item
        POST /api/v1/items/:id/votes
        """
        try:
            # Get the item
            item = DecisionItem.objects.get(pk=item_id)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to vote on this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if decision is closed
            if item.decision.status == 'closed':
                return Response({
                    'status': 'error',
                    'message': 'Cannot vote on items in a closed decision'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if vote already exists
            existing_vote = DecisionVote.objects.filter(
                item=item,
                user=request.user
            ).first()
            
            if existing_vote:
                # Update existing vote
                serializer = self.get_serializer(existing_vote, data=request.data, partial=True)
                
                if not serializer.is_valid():
                    return Response({
                        'status': 'error',
                        'message': 'Vote update failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                vote = serializer.save()
                
                return Response({
                    'status': 'success',
                    'data': DecisionVoteSerializer(vote).data
                }, status=status.HTTP_200_OK)
            else:
                # Create new vote
                data = request.data.copy()
                data['item'] = item.id
                
                serializer = self.get_serializer(data=data)
                
                if not serializer.is_valid():
                    return Response({
                        'status': 'error',
                        'message': 'Vote creation failed',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Save with the current user
                vote = serializer.save(user=request.user)
                
                return Response({
                    'status': 'success',
                    'data': DecisionVoteSerializer(vote).data
                }, status=status.HTTP_201_CREATED)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='items/(?P<item_id>[^/.]+)/votes/me')
    def get_my_vote(self, request, item_id=None):
        """
        Get current user's vote on an item
        GET /api/v1/items/:id/votes/me
        """
        try:
            # Get the item
            item = DecisionItem.objects.get(pk=item_id)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to access this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get the vote
            vote = DecisionVote.objects.filter(
                item=item,
                user=request.user
            ).first()
            
            if vote:
                serializer = self.get_serializer(vote)
                return Response({
                    'status': 'success',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'success',
                    'data': None,
                    'message': 'No vote found'
                }, status=status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='items/(?P<item_id>[^/.]+)/votes/summary')
    def get_vote_summary(self, request, item_id=None):
        """
        Get aggregate vote statistics for an item
        GET /api/v1/items/:id/votes/summary
        """
        try:
            # Get the item with related decision and group
            item = DecisionItem.objects.select_related(
                'decision__group'
            ).get(pk=item_id)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to access this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get all votes for this item
            votes = DecisionVote.objects.filter(item=item)
            
            # Calculate statistics
            total_votes = votes.count()
            likes = votes.filter(is_like=True).count()
            dislikes = votes.filter(is_like=False).count()
            
            # Calculate average rating
            rating_votes = votes.filter(rating__isnull=False)
            rating_count = rating_votes.count()
            
            if rating_count > 0:
                from django.db.models import Avg
                average_rating = rating_votes.aggregate(Avg('rating'))['rating__avg']
            else:
                average_rating = None
            
            summary_data = {
                'total_votes': total_votes,
                'likes': likes,
                'dislikes': dislikes,
                'average_rating': average_rating,
                'rating_count': rating_count
            }
            
            serializer = VoteSummarySerializer(summary_data)
            
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)/votes')
    def delete_vote(self, request, item_id=None):
        """
        Delete current user's vote on an item (for undo functionality)
        DELETE /api/v1/votes/items/:id/votes
        """
        try:
            item = DecisionItem.objects.get(pk=item_id)
            
            # Check if user is a confirmed member of the decision's group
            membership = GroupMembership.objects.filter(
                group=item.decision.group,
                user=request.user,
                is_confirmed=True
            ).first()
            
            if not membership:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to access this item'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if decision is closed
            if item.decision.status == 'closed':
                return Response({
                    'status': 'error',
                    'message': 'Cannot modify votes on items in a closed decision'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Delete the vote
            deleted_count, _ = DecisionVote.objects.filter(
                item=item,
                user=request.user
            ).delete()
            
            if deleted_count > 0:
                return Response({
                    'status': 'success',
                    'message': 'Vote deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'No vote found to delete'
                }, status=status.HTTP_404_NOT_FOUND)
            
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for question operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    
    def list(self, request):
        """
        List questions with optional scope filtering
        GET /api/v1/questions?scope=global&item_type=car&decision_id=uuid&group_id=uuid
        """
        queryset = Question.objects.all()
        
        # Filter by scope
        scope = request.query_params.get('scope', None)
        if scope:
            queryset = queryset.filter(scope=scope)
        
        # Filter by item_type (for item_type scoped questions)
        item_type = request.query_params.get('item_type', None)
        if item_type:
            queryset = queryset.filter(item_type=item_type)
        
        # For decision-scoped questions, we just filter by scope
        # The frontend will need to know which questions to show based on the decision context
        
        # Order by created_at
        queryset = queryset.order_by('created_at')
        
        serializer = QuestionSerializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UserAnswerViewSet(viewsets.GenericViewSet):
    """ViewSet for user answer operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAnswerSerializer
    
    @action(detail=False, methods=['post'], url_path='submit')
    def submit_answer(self, request):
        """
        Submit an answer to a question
        POST /api/v1/answers/submit
        
        Body:
        {
            "question": "uuid",
            "decision": "uuid" (optional),
            "answer_option": "uuid" (optional),
            "answer_value": {} (optional)
        }
        """
        serializer = UserAnswerCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        question_id = serializer.validated_data['question'].id
        decision_id = serializer.validated_data.get('decision')
        decision_id = decision_id.id if decision_id else None
        
        # Check if answer already exists (update instead of create)
        existing_answer = UserAnswer.objects.filter(
            user=request.user,
            question_id=question_id,
            decision_id=decision_id
        ).first()
        
        if existing_answer:
            # Update existing answer
            update_serializer = UserAnswerSerializer(
                existing_answer,
                data=request.data,
                partial=True
            )
            
            if update_serializer.is_valid():
                update_serializer.save()
                
                return Response({
                    'status': 'success',
                    'data': update_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'message': 'Invalid data',
                'errors': update_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new answer
        answer = UserAnswer.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        response_serializer = UserAnswerSerializer(answer)
        
        return Response({
            'status': 'success',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'], url_path='my-answers')
    def my_answers(self, request):
        """
        Get current user's answers
        GET /api/v1/answers/my-answers?question=uuid&decision=uuid
        """
        queryset = UserAnswer.objects.filter(user=request.user)
        
        # Filter by question
        question_id = request.query_params.get('question', None)
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        # Filter by decision
        decision_id = request.query_params.get('decision', None)
        if decision_id:
            queryset = queryset.filter(decision_id=decision_id)
        
        serializer = UserAnswerSerializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class GenerationViewSet(viewsets.GenericViewSet):
    """ViewSet for character image generation operations"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter generation jobs based on user's group membership"""
        from core.models import GenerationJob
        
        user = self.request.user
        
        # Get all groups where user is a confirmed member
        user_groups = AppGroup.objects.filter(
            memberships__user=user,
            memberships__is_confirmed=True
        )
        
        # Return generation jobs from items in decisions in those groups
        return GenerationJob.objects.filter(
            item__decision__group__in=user_groups
        ).select_related('item', 'item__decision')
    
    @action(detail=False, methods=['post'], url_path='decisions/(?P<decision_id>[^/.]+)/generate')
    def create_generation(self, request, decision_id=None):
        """
        Create a new character with image generation
        POST /api/v1/generations/decisions/:decision_id/generate
        
        Request body:
        {
            "description": "friendly robot sidekick",
            "art_style": "cartoon",
            "view_angle": "side_profile",
            "pose": "idle",
            "expression": "happy",
            "background": "transparent",
            "color_palette": "vibrant"
        }
        """
        from core.models import GenerationJob
        from core.serializers import GenerationRequestSerializer, GenerationJobSerializer
        from core.services.generation import GenerationJobProcessor, GenerationJobProcessorError
        
        # Verify decision exists and user has access
        try:
            decision = Decision.objects.get(pk=decision_id)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to create items in this decision'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate request parameters
        serializer = GenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid generation parameters',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        params = serializer.validated_data
        
        # Validate and apply locked parameters from decision
        locked_params = decision.get_locked_params()
        if locked_params:
            # Check for conflicts with locked parameters
            for param_name, locked_value in locked_params.items():
                provided_value = params.get(param_name)
                if provided_value is not None and provided_value != locked_value:
                    return Response({
                        'status': 'error',
                        'message': f'Parameter "{param_name}" is locked to "{locked_value}" for this decision. '
                                  f'Cannot set to "{provided_value}".'
                    }, status=status.HTTP_400_BAD_REQUEST)
                # Apply locked value
                params[param_name] = locked_value
        
        # Create the DecisionItem first
        item = DecisionItem.objects.create(
            decision=decision,
            label=params['description'][:255],  # Use description as label
            attributes={
                'type': '2d_character',
                'description': params['description'],
                'generation_params': {
                    'art_style': params['art_style'],
                    'view_angle': params['view_angle'],
                    'pose': params.get('pose', 'idle'),
                    'expression': params.get('expression', 'neutral'),
                    'background': params.get('background', 'transparent'),
                    'color_palette': params.get('color_palette', 'vibrant'),
                },
                'image_url': None,
                'parent_item_id': None,
                'version': 1
            }
        )
        
        # Create and submit the generation job
        try:
            processor = GenerationJobProcessor()
            job = processor.create_job(item=item, parameters=params)
            
            job_serializer = GenerationJobSerializer(job)
            
            return Response({
                'status': 'success',
                'message': 'Character generation started',
                'data': job_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except GenerationJobProcessorError as e:
            # Clean up the item if job creation failed
            item.delete()
            
            return Response({
                'status': 'error',
                'message': f'Failed to start generation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='jobs/(?P<job_id>[^/.]+)/status')
    def get_status(self, request, job_id=None):
        """
        Get generation job status
        GET /api/v1/generations/jobs/:job_id/status
        """
        from core.models import GenerationJob
        from core.serializers import GenerationJobSerializer
        
        try:
            job = self.get_queryset().get(pk=job_id)
        except GenerationJob.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Generation job not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GenerationJobSerializer(job)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='jobs/(?P<job_id>[^/.]+)/retry')
    def retry_generation(self, request, job_id=None):
        """
        Retry a failed generation job
        POST /api/v1/generations/jobs/:job_id/retry
        """
        from core.models import GenerationJob
        from core.serializers import GenerationJobSerializer
        from core.services.generation import GenerationJobProcessor, GenerationJobProcessorError
        
        try:
            job = self.get_queryset().get(pk=job_id)
        except GenerationJob.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Generation job not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if job.status != 'failed':
            return Response({
                'status': 'error',
                'message': f'Can only retry failed jobs. Current status: {job.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            processor = GenerationJobProcessor()
            new_job = processor.retry_job(job)
            
            serializer = GenerationJobSerializer(new_job)
            
            return Response({
                'status': 'success',
                'message': 'Generation retry started',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except GenerationJobProcessorError as e:
            return Response({
                'status': 'error',
                'message': f'Failed to retry generation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='decisions/(?P<decision_id>[^/.]+)/stats')
    def get_decision_stats(self, request, decision_id=None):
        """
        Get generation statistics for a decision
        GET /api/v1/generations/decisions/:decision_id/stats
        """
        from core.serializers import GenerationStatusSerializer
        from core.services.generation import GenerationJobProcessor
        
        # Verify decision exists and user has access
        try:
            decision = Decision.objects.get(pk=decision_id)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this decision'
            }, status=status.HTTP_403_FORBIDDEN)
        
        processor = GenerationJobProcessor()
        stats = processor.get_decision_generation_stats(decision_id)
        
        serializer = GenerationStatusSerializer(data=stats)
        serializer.is_valid()
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='decisions/(?P<decision_id>[^/.]+)/jobs')
    def list_decision_jobs(self, request, decision_id=None):
        """
        List all generation jobs for a decision
        GET /api/v1/generations/decisions/:decision_id/jobs
        """
        from core.models import GenerationJob
        from core.serializers import GenerationJobSerializer
        
        # Verify decision exists and user has access
        try:
            decision = Decision.objects.get(pk=decision_id)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this decision'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get jobs for this decision
        jobs = GenerationJob.objects.filter(
            item__decision_id=decision_id
        ).select_related('item', 'item__decision').order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            jobs = jobs.filter(status=status_filter)
        
        serializer = GenerationJobSerializer(jobs, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/variation')
    def create_variation(self, request, item_id=None):
        """
        Create a variation of an existing character item
        POST /api/v1/generations/items/:item_id/variation
        
        Request body (all fields optional - will inherit from parent if not provided):
        {
            "description": "friendly robot sidekick with wings",
            "art_style": "cartoon",
            "view_angle": "side_profile",
            "pose": "jumping",
            "expression": "happy",
            "background": "transparent",
            "color_palette": "vibrant"
        }
        
        Locked parameters from the decision cannot be modified.
        """
        from core.models import GenerationJob
        from core.serializers import GenerationJobSerializer, VariationRequestSerializer
        from core.services.generation import GenerationJobProcessor, GenerationJobProcessorError
        
        # Get the parent item
        try:
            parent_item = DecisionItem.objects.select_related('decision', 'decision__group').get(pk=item_id)
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if it's a character item
        if not parent_item.is_character_item():
            return Response({
                'status': 'error',
                'message': 'Can only create variations of 2D character items'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        decision = parent_item.decision
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to create variations in this decision'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get parent's generation parameters
        parent_params = parent_item.get_generation_params()
        parent_description = parent_item.attributes.get('description', parent_item.label)
        
        # Validate request parameters (all optional for variations)
        serializer = VariationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'message': 'Invalid variation parameters',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Merge parent params with provided params (provided params override)
        variation_params = {
            'description': serializer.validated_data.get('description') or parent_description,
            'art_style': serializer.validated_data.get('art_style') or parent_params.get('art_style', 'cartoon'),
            'view_angle': serializer.validated_data.get('view_angle') or parent_params.get('view_angle', 'side_profile'),
            'pose': serializer.validated_data.get('pose') or parent_params.get('pose', 'idle'),
            'expression': serializer.validated_data.get('expression') or parent_params.get('expression', 'neutral'),
            'background': serializer.validated_data.get('background') or parent_params.get('background', 'transparent'),
            'color_palette': serializer.validated_data.get('color_palette') or parent_params.get('color_palette', 'vibrant'),
        }
        
        # Validate and apply locked parameters from decision
        locked_params = decision.get_locked_params()
        if locked_params:
            # Check for conflicts with locked parameters
            for param_name, locked_value in locked_params.items():
                provided_value = serializer.validated_data.get(param_name)
                if provided_value is not None and provided_value != locked_value:
                    return Response({
                        'status': 'error',
                        'message': f'Parameter "{param_name}" is locked to "{locked_value}" for this decision. '
                                  f'Cannot set to "{provided_value}".'
                    }, status=status.HTTP_400_BAD_REQUEST)
                # Apply locked value
                variation_params[param_name] = locked_value
        
        # Calculate version number
        parent_version = parent_item.get_version()
        new_version = parent_version + 1
        
        # Create the new DecisionItem as a variation
        variation_item = DecisionItem.objects.create(
            decision=decision,
            label=variation_params['description'][:255],
            attributes={
                'type': '2d_character',
                'description': variation_params['description'],
                'generation_params': {
                    'art_style': variation_params['art_style'],
                    'view_angle': variation_params['view_angle'],
                    'pose': variation_params['pose'],
                    'expression': variation_params['expression'],
                    'background': variation_params['background'],
                    'color_palette': variation_params['color_palette'],
                },
                'image_url': None,
                'parent_item_id': str(parent_item.id),
                'version': new_version
            }
        )
        
        # Create and submit the generation job
        try:
            processor = GenerationJobProcessor()
            job = processor.create_job(item=variation_item, parameters=variation_params)
            
            job_serializer = GenerationJobSerializer(job)
            
            return Response({
                'status': 'success',
                'message': 'Character variation generation started',
                'data': {
                    'job': job_serializer.data,
                    'parent_item_id': str(parent_item.id),
                    'version': new_version,
                    'param_changes': {
                        k: v for k, v in variation_params.items()
                        if k != 'description' and v != parent_params.get(k)
                    }
                }
            }, status=status.HTTP_201_CREATED)
            
        except GenerationJobProcessorError as e:
            # Clean up the item if job creation failed
            variation_item.delete()
            
            return Response({
                'status': 'error',
                'message': f'Failed to start variation generation: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='items/(?P<item_id>[^/.]+)/versions')
    def get_item_versions(self, request, item_id=None):
        """
        Get version information for a character item
        GET /api/v1/generations/items/:item_id/versions
        
        Returns the version chain and all variations of the item.
        """
        from core.serializers import DecisionItemSerializer
        
        # Get the item
        try:
            item = DecisionItem.objects.select_related('decision', 'decision__group').get(pk=item_id)
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=item.decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this item'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get version chain (ancestors)
        version_chain = item.get_version_chain()
        
        # Get direct children (variations)
        children = item.get_child_items()
        
        # Get root item
        root_item = item.get_root_item()
        
        # Get param diff from parent
        param_diff = item.get_param_diff_from_parent()
        
        return Response({
            'status': 'success',
            'data': {
                'item_id': str(item.id),
                'version': item.get_version(),
                'parent_item_id': item.get_parent_item_id(),
                'root_item_id': str(root_item.id),
                'variation_count': item.get_variation_count(),
                'version_chain': [
                    {
                        'id': str(v.id),
                        'label': v.label,
                        'version': v.get_version(),
                    }
                    for v in version_chain
                ],
                'children': [
                    {
                        'id': str(c.id),
                        'label': c.label,
                        'version': c.get_version(),
                    }
                    for c in children
                ],
                'param_diff_from_parent': {
                    k: {'parent': v[0], 'current': v[1]}
                    for k, v in param_diff.items()
                }
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='jobs/(?P<job_id>[^/.]+)/timeout')
    def timeout_job(self, request, job_id=None):
        """
        Mark a generation job as timed out and delete the associated item.
        POST /api/v1/generations/jobs/:job_id/timeout/
        
        This endpoint is called by the frontend when a job has been pending/processing
        for too long (e.g., 40 seconds). It marks the job as failed and deletes
        the associated DecisionItem to clean up stale entries.
        
        Returns the description of the deleted item so the frontend can show
        a notification to the user.
        """
        from core.models import GenerationJob
        
        # Get the job
        try:
            job = GenerationJob.objects.select_related('item', 'item__decision', 'item__decision__group').get(pk=job_id)
        except GenerationJob.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Generation job not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a confirmed member of the decision's group
        membership = GroupMembership.objects.filter(
            group=job.item.decision.group,
            user=request.user,
            is_confirmed=True
        ).first()
        
        if not membership:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this job'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Only timeout jobs that are still pending or processing
        if job.status not in ['pending', 'processing']:
            return Response({
                'status': 'error',
                'message': f'Job is already {job.status}, cannot timeout'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get item info before deletion
        item = job.item
        item_description = item.attributes.get('description', item.label) if item.attributes else item.label
        item_id = str(item.id)
        
        # Mark job as failed with timeout message
        job.status = 'failed'
        job.error_message = 'Generation timed out after 40 seconds'
        job.save(update_fields=['status', 'error_message', 'updated_at'])
        
        # Delete the associated item
        item.delete()
        
        return Response({
            'status': 'success',
            'message': f'Generation for "{item_description}" timed out and was removed',
            'data': {
                'job_id': str(job_id),
                'item_id': item_id,
                'item_description': item_description,
            }
        }, status=status.HTTP_200_OK)


class ExportViewSet(viewsets.GenericViewSet):
    """ViewSet for exporting character images and parameters"""
    permission_classes = [IsAuthenticated]
    
    def _get_user_groups(self, user):
        """Get all groups where user is a confirmed member"""
        return AppGroup.objects.filter(
            memberships__user=user,
            memberships__is_confirmed=True
        )
    
    def _check_item_access(self, item, user):
        """Check if user has access to the item's decision"""
        user_groups = self._get_user_groups(user)
        return item.decision.group in user_groups
    
    def _check_decision_access(self, decision, user):
        """Check if user has access to the decision"""
        user_groups = self._get_user_groups(user)
        return decision.group in user_groups
    
    @action(detail=False, methods=['get'], url_path='items/(?P<item_id>[^/.]+)/image')
    def download_image(self, request, item_id=None):
        """
        Download the image file for a character item
        GET /api/v1/exports/items/:item_id/image
        
        Returns the image file with appropriate Content-Disposition header.
        """
        import requests
        from django.http import HttpResponse
        from core.utils import derive_filename_from_description
        
        # Get the item
        try:
            item = DecisionItem.objects.select_related('decision', 'decision__group').get(pk=item_id)
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check access
        if not self._check_item_access(item, request.user):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this item'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if it's a character item with an image
        if not item.is_character_item():
            return Response({
                'status': 'error',
                'message': 'This item is not a character item'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attributes = item.attributes or {}
        image_url = attributes.get('image_url')
        
        if not image_url:
            return Response({
                'status': 'error',
                'message': 'No image available for this item'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Generate filename
        description = attributes.get('description', item.label)
        version = attributes.get('version', 1)
        filename = derive_filename_from_description(description, version, 'png')
        
        try:
            # Fetch the image from the URL
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            # Determine content type
            content_type = image_response.headers.get('Content-Type', 'image/png')
            
            # Create response with image data
            response = HttpResponse(
                image_response.content,
                content_type=content_type
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(image_response.content)
            
            return response
            
        except requests.RequestException as e:
            return Response({
                'status': 'error',
                'message': f'Failed to download image: {str(e)}'
            }, status=status.HTTP_502_BAD_GATEWAY)
    
    @action(detail=False, methods=['get'], url_path='items/(?P<item_id>[^/.]+)/json')
    def export_json(self, request, item_id=None):
        """
        Export character parameters as JSON
        GET /api/v1/exports/items/:item_id/json
        
        Returns JSON file with all generation parameters, description, and metadata.
        """
        import json
        from django.http import HttpResponse
        from core.utils import derive_json_filename_from_description
        from core.serializers import CharacterExportSerializer
        
        # Get the item
        try:
            item = DecisionItem.objects.select_related('decision', 'decision__group').get(pk=item_id)
        except DecisionItem.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Item not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check access
        if not self._check_item_access(item, request.user):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this item'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if it's a character item
        if not item.is_character_item():
            return Response({
                'status': 'error',
                'message': 'This item is not a character item'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build export data
        attributes = item.attributes or {}
        export_data = CharacterExportSerializer.from_decision_item(item, creator_username=None)
        
        # Convert UUIDs and datetimes to strings for JSON serialization
        export_data['id'] = str(export_data['id'])
        export_data['decision_id'] = str(export_data['decision_id'])
        if export_data['created_at']:
            export_data['created_at'] = export_data['created_at'].isoformat()
        
        # Generate filename
        description = attributes.get('description', item.label)
        version = attributes.get('version', 1)
        filename = derive_json_filename_from_description(description, version)
        
        # Create JSON response
        json_content = json.dumps(export_data, indent=2)
        
        response = HttpResponse(
            json_content,
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(json_content.encode('utf-8'))
        
        return response
    
    @action(detail=False, methods=['get'], url_path='decisions/(?P<decision_id>[^/.]+)/batch')
    def batch_export(self, request, decision_id=None):
        """
        Export all approved characters (favourites) as a ZIP file
        GET /api/v1/exports/decisions/:decision_id/batch
        
        Returns a ZIP file containing:
        - All character images (PNG files)
        - All character parameters (JSON files)
        - A manifest.json with the list of all exported characters
        """
        import io
        import json
        import zipfile
        import requests
        from django.http import HttpResponse
        from core.utils import derive_filename_from_description, derive_json_filename_from_description
        from core.serializers import CharacterExportSerializer
        
        # Get the decision
        try:
            decision = Decision.objects.select_related('group').get(pk=decision_id)
        except Decision.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Decision not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check access
        if not self._check_decision_access(decision, request.user):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to access this decision'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all favourites (approved characters) for this decision
        favourites = DecisionSelection.objects.filter(
            decision=decision
        ).select_related('item', 'item__decision')
        
        # Filter to only character items
        character_favourites = [
            fav for fav in favourites 
            if fav.item.is_character_item()
        ]
        
        if not character_favourites:
            return Response({
                'status': 'error',
                'message': 'No approved character items found in this decision'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        manifest_entries = []
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for fav in character_favourites:
                item = fav.item
                attributes = item.attributes or {}
                description = attributes.get('description', item.label)
                version = attributes.get('version', 1)
                
                # Generate filenames
                image_filename = derive_filename_from_description(description, version, 'png')
                json_filename = derive_json_filename_from_description(description, version)
                
                # Build export data for JSON
                export_data = CharacterExportSerializer.from_decision_item(item)
                export_data['id'] = str(export_data['id'])
                export_data['decision_id'] = str(export_data['decision_id'])
                if export_data['created_at']:
                    export_data['created_at'] = export_data['created_at'].isoformat()
                
                # Add JSON to ZIP
                json_content = json.dumps(export_data, indent=2)
                zip_file.writestr(f'parameters/{json_filename}', json_content)
                
                # Try to download and add image
                image_url = attributes.get('image_url')
                image_added = False
                
                if image_url:
                    try:
                        image_response = requests.get(image_url, timeout=30)
                        image_response.raise_for_status()
                        zip_file.writestr(f'images/{image_filename}', image_response.content)
                        image_added = True
                    except requests.RequestException:
                        # Skip image if download fails, but continue with export
                        pass
                
                # Add to manifest
                manifest_entries.append({
                    'id': str(item.id),
                    'description': description,
                    'version': version,
                    'image_filename': f'images/{image_filename}' if image_added else None,
                    'json_filename': f'parameters/{json_filename}',
                    'selected_at': fav.selected_at.isoformat() if fav.selected_at else None,
                })
            
            # Add manifest
            manifest = {
                'decision_id': str(decision.id),
                'decision_title': decision.title,
                'exported_at': timezone.now().isoformat(),
                'total_characters': len(manifest_entries),
                'characters': manifest_entries,
            }
            zip_file.writestr('manifest.json', json.dumps(manifest, indent=2))
        
        # Prepare response
        zip_buffer.seek(0)
        
        # Generate ZIP filename
        decision_name = decision.title.lower().replace(' ', '_')[:50]
        zip_filename = f'{decision_name}_characters_export.zip'
        
        response = HttpResponse(
            zip_buffer.getvalue(),
            content_type='application/zip'
        )
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        response['Content-Length'] = len(zip_buffer.getvalue())
        
        return response
