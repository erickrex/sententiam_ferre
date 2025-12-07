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
    Conversation, Message, Question, AnswerOption, UserAnswer
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
    ConversationSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    MessageUpdateSerializer,
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
    
    @action(detail=True, methods=['get'], url_path='conversation')
    def get_conversation(self, request, pk=None):
        """
        Get or create conversation for a decision
        GET /api/v1/decisions/:id/conversation
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            # Get or create conversation
            conversation, created = Conversation.objects.get_or_create(decision=decision)
            
            serializer = ConversationSerializer(conversation)
            
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
    
    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        List or send messages in a decision's conversation
        GET /api/v1/decisions/:id/messages - List messages
        POST /api/v1/decisions/:id/messages - Send a message
        """
        try:
            decision = self.get_queryset().get(pk=pk)
            
            if request.method == 'POST':
                # Send a message
                # Get or create conversation
                conversation, created = Conversation.objects.get_or_create(decision=decision)
                
                # Create message
                message_data = {
                    'conversation': conversation.id,
                    'text': request.data.get('text')
                }
                
                serializer = MessageCreateSerializer(data=message_data)
                
                if serializer.is_valid():
                    message = serializer.save(sender=request.user)
                    
                    # Return the created message with full details
                    response_serializer = MessageSerializer(message)
                    
                    return Response({
                        'status': 'success',
                        'data': response_serializer.data
                    }, status=status.HTTP_201_CREATED)
                
                return Response({
                    'status': 'error',
                    'message': 'Invalid message data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            else:  # GET
                # List messages
                # Get conversation
                try:
                    conversation = Conversation.objects.get(decision=decision)
                except Conversation.DoesNotExist:
                    # No conversation yet, return empty list
                    return Response({
                        'status': 'success',
                        'data': {
                            'results': [],
                            'count': 0
                        }
                    }, status=status.HTTP_200_OK)
                
                # Get messages ordered by sent_at with sender info
                messages = Message.objects.filter(
                    conversation=conversation
                ).select_related('sender').order_by('sent_at')
                
                # Apply pagination if needed
                page = request.query_params.get('page')
                page_size = request.query_params.get('page_size', 50)
                
                if page:
                    from django.core.paginator import Paginator
                    paginator = Paginator(messages, page_size)
                    page_obj = paginator.get_page(page)
                    serializer = MessageSerializer(page_obj, many=True)
                    
                    return Response({
                        'status': 'success',
                        'data': {
                            'results': serializer.data,
                            'count': paginator.count,
                            'page': page_obj.number,
                            'total_pages': paginator.num_pages
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    serializer = MessageSerializer(messages, many=True)
                    
                    return Response({
                        'status': 'success',
                        'data': {
                            'results': serializer.data,
                            'count': messages.count()
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



class MessageViewSet(viewsets.GenericViewSet):
    """ViewSet for message operations"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    
    @action(detail=True, methods=['patch'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark a message as read
        PATCH /api/v1/messages/:id/mark-read
        """
        try:
            # Get the message
            message = Message.objects.get(pk=pk)
            
            # Check if user is a confirmed member of the decision's group
            decision = message.conversation.decision
            
            # Check if user is a confirmed member of the decision's group or shared groups
            is_member = GroupMembership.objects.filter(
                group=decision.group,
                user=request.user,
                is_confirmed=True
            ).exists()
            
            if not is_member:
                # Check if user is in a shared group
                from core.models import DecisionSharedGroup
                shared_groups = DecisionSharedGroup.objects.filter(
                    decision=decision
                ).values_list('group_id', flat=True)
                
                is_member = GroupMembership.objects.filter(
                    group_id__in=shared_groups,
                    user=request.user,
                    is_confirmed=True
                ).exists()
            
            if not is_member:
                return Response({
                    'status': 'error',
                    'message': 'You do not have permission to access this message'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Update the message
            serializer = MessageUpdateSerializer(message, data={'is_read': True}, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                # Return the updated message
                response_serializer = MessageSerializer(message)
                
                return Response({
                    'status': 'success',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                'status': 'error',
                'message': 'Invalid data',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Message.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Message not found'
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
