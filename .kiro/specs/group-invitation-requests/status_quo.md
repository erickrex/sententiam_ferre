# Status Quo: Current Group Invitation System

## Overview
This document describes the current state of the group invitation system in Sententiam Ferre before implementing the enhanced invitation and join request features.

## Current System Architecture

### Backend (Django)

**Models:**
- `AppGroup`: Represents a group with name, description, and creator
- `GroupMembership`: Links users to groups with the following fields:
  - `group`: Foreign key to AppGroup
  - `user`: Foreign key to UserAccount
  - `role`: Either 'admin' or 'member'
  - `is_confirmed`: Boolean indicating if invitation was accepted
  - `invited_at`: Timestamp of invitation creation
  - `confirmed_at`: Timestamp when invitation was accepted

**Current Invitation Flow:**
1. **Group Creation**: When a user creates a group, they automatically become an admin member with `is_confirmed=True`
2. **Admin Invites User**: Admin can invite users by username, email, or user_id
3. **Invitation Created**: System creates a `GroupMembership` record with `is_confirmed=False`
4. **User Accepts/Declines**: 
   - Accept: Updates `is_confirmed=True` and sets `confirmed_at`
   - Decline: Deletes the `GroupMembership` record

**API Endpoints:**
- `GET /api/v1/groups/` - List user's groups (only confirmed memberships)
- `POST /api/v1/groups/` - Create new group
- `GET /api/v1/groups/:id/` - Get group details
- `GET /api/v1/groups/:id/members/` - List all members (confirmed and pending)
- `POST /api/v1/groups/:id/members/` - Invite user to group (admin only)
- `PATCH /api/v1/groups/:id/members/:userId/` - Accept/decline invitation
- `DELETE /api/v1/groups/:id/members/:userId/` - Remove member or cancel invitation

### Frontend (React)

**Current UI Structure:**
- **GroupsPage**: Single view showing user's groups with "+ Create Group" button
- **GroupDetailPage**: Shows group with tabs for "Decisions" and "Members"
- **GroupDetail Component**: Displays:
  - Confirmed members list
  - Pending invitations (for admins)
  - "+ Invite Member" button (admin only)
- **InviteModal**: Form for admins to invite users by username

**Current User Flows:**

1. **Creating a Group:**
   - User clicks "+ Create Group" on Groups page
   - Fills in name and description
   - Becomes admin automatically

2. **Inviting Members (Admin):**
   - Admin opens group detail page
   - Clicks "Members" tab
   - Clicks "+ Invite Member"
   - Enters username in modal
   - System creates pending invitation

3. **Accepting Invitation (User):**
   - User sees invitation banner on group detail page
   - Clicks "Accept" or "Decline"
   - Accept: Becomes confirmed member
   - Decline: Invitation is deleted

## Current Limitations

1. **No User-Initiated Join Requests**: Users cannot request to join a group; they must wait for an invitation
2. **No Group Discovery**: Users cannot browse or search for groups to join
3. **Limited Invitation Management**: 
   - No way to resend declined invitations
   - No history of rejected invitations
   - Admins cannot see if an invitation was declined vs. pending
4. **Single Invitation Method**: Only admin-initiated invitations exist
5. **No Request Queue**: No concept of users requesting to join groups
6. **UI Organization**: Groups page only shows "My Groups" - no join/discover functionality

## Data Model

**Current GroupMembership States:**
- `is_confirmed=False`: Pending invitation (admin invited, user hasn't responded)
- `is_confirmed=True`: Active member

**Missing States:**
- No distinction between admin-invited vs. user-requested
- No "rejected" state (rejections delete the record)
- No way to track rejection history or allow resending

## Technical Constraints

1. **Unique Constraint**: `(group, user)` must be unique in GroupMembership
2. **Deletion on Decline**: Current system deletes membership records when declined
3. **No Audit Trail**: No history of invitation/request actions
4. **Single Direction**: Only admin → user invitations, not user → admin requests

## Summary

The current system supports a simple admin-initiated invitation flow where:
- Admins invite users
- Users accept or decline
- Declined invitations are deleted
- No user-initiated join requests exist
- No invitation/request history or resend capability

This status quo document serves as the baseline for designing the enhanced invitation and join request system.
