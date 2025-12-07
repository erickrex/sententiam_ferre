"""
Custom permission classes for authorization
"""
from rest_framework import permissions
from core.models import GroupMembership, DecisionSharedGroup


class IsGroupMember(permissions.BasePermission):
    """
    Permission class to check if user is a confirmed member of a group.
    
    This permission expects the view to have a 'get_group' method that returns
    the group to check membership for, or it will look for 'group_id' in view kwargs.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a confirmed member of the object's group"""
        # Get the group from the object
        group = None
        
        if hasattr(obj, 'group'):
            group = obj.group
        elif hasattr(obj, 'decision') and hasattr(obj.decision, 'group'):
            group = obj.decision.group
        elif hasattr(obj, 'item') and hasattr(obj.item, 'decision'):
            group = obj.item.decision.group
        
        if not group:
            return False
        
        # Check if user is a confirmed member
        return GroupMembership.objects.filter(
            group=group,
            user=request.user,
            is_confirmed=True
        ).exists()


class IsDecisionParticipant(permissions.BasePermission):
    """
    Permission class to check if user can participate in a decision.
    
    User must be a confirmed member of either:
    - The decision's owning group, OR
    - A group the decision is shared with
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access the decision"""
        # Get the decision from the object
        decision = None
        
        if hasattr(obj, 'decision'):
            decision = obj.decision
        elif hasattr(obj, 'item') and hasattr(obj.item, 'decision'):
            decision = obj.item.decision
        elif hasattr(obj, 'id') and obj.__class__.__name__ == 'Decision':
            decision = obj
        
        if not decision:
            return False
        
        # Check if user is a confirmed member of the owning group
        is_owner_member = GroupMembership.objects.filter(
            group=decision.group,
            user=request.user,
            is_confirmed=True
        ).exists()
        
        if is_owner_member:
            return True
        
        # Check if user is a confirmed member of any shared group
        shared_group_ids = DecisionSharedGroup.objects.filter(
            decision=decision
        ).values_list('group_id', flat=True)
        
        is_shared_member = GroupMembership.objects.filter(
            group_id__in=shared_group_ids,
            user=request.user,
            is_confirmed=True
        ).exists()
        
        return is_shared_member


class IsGroupAdmin(permissions.BasePermission):
    """
    Permission class to check if user is an admin of a group.
    
    This permission checks if the user is a confirmed member with 'admin' role.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is an admin of the object's group"""
        # Get the group from the object
        group = None
        
        if hasattr(obj, 'group'):
            group = obj.group
        elif hasattr(obj, 'decision') and hasattr(obj.decision, 'group'):
            group = obj.decision.group
        elif hasattr(obj, 'item') and hasattr(obj.item, 'decision'):
            group = obj.item.decision.group
        
        if not group:
            return False
        
        # Check if user is a confirmed admin
        try:
            membership = GroupMembership.objects.get(
                group=group,
                user=request.user,
                is_confirmed=True
            )
            return membership.role == 'admin'
        except GroupMembership.DoesNotExist:
            return False
