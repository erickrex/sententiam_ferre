# Requirements Document

## Introduction

This specification enhances the Sententiam Ferre group membership system by adding bidirectional invitation and join request capabilities. The system will support both admin-initiated invitations and user-initiated join requests, with comprehensive management features for both parties including rejection handling, resend capabilities, and improved UI organization.

## Glossary

- **System**: The Sententiam Ferre application
- **User**: An authenticated person who can join groups
- **Admin**: A group member with administrative privileges
- **Invitation**: An admin-initiated request for a user to join a group
- **Join Request**: A user-initiated request to join a specific group
- **Pending Invitation**: An invitation that has been sent but not yet accepted or rejected
- **Pending Request**: A join request that has been submitted but not yet approved or rejected
- **Rejected Invitation**: An invitation that the invited user has declined
- **Rejected Request**: A join request that an admin has declined
- **GroupMembership**: Database record linking a user to a group with status information
- **Membership Type**: Either 'invitation' (admin-initiated) or 'request' (user-initiated)
- **Membership Status**: Current state - 'pending', 'confirmed', or 'rejected'

## Requirements

### Requirement 1

**User Story:** As a user, I want to see separate tabs for joining groups and creating groups, so that I can easily discover and request to join existing groups.

#### Acceptance Criteria

1. WHEN a user navigates to the groups page THEN the System SHALL display two tabs: "Join" and "Create"
2. THE System SHALL display the "Join" tab as the first (default) tab
3. THE System SHALL display the "Create" tab as the second tab
4. WHEN a user clicks the "Join" tab THEN the System SHALL display join-related functionality
5. WHEN a user clicks the "Create" tab THEN the System SHALL display the group creation form

### Requirement 2

**User Story:** As a user, I want to request to join a group by entering its name, so that I can become a member without waiting for an invitation.

#### Acceptance Criteria

1. WHEN a user is on the "Join" tab THEN the System SHALL display a "Requests" section with an input field for group name
2. WHEN a user enters a valid group name and clicks "Request" THEN the System SHALL create a join request with membership_type='request' and status='pending'
3. WHEN a user enters a non-existent group name THEN the System SHALL display an error message "Group not found"
4. WHEN a user attempts to request to join a group they are already a member of THEN the System SHALL display an error message "You are already a member of this group"
5. WHEN a user attempts to request to join a group with a pending request THEN the System SHALL display an error message "You already have a pending request for this group"
6. THE System SHALL validate that the group name is not empty before allowing submission

### Requirement 3

**User Story:** As a user, I want to view my pending and rejected join requests, so that I can track the status of my membership applications.

#### Acceptance Criteria

1. WHEN a user is on the "Join" tab THEN the System SHALL display a list of all join requests with status='pending' or status='rejected'
2. WHEN displaying a pending request THEN the System SHALL show the group name, request date, and status badge
3. WHEN displaying a rejected request THEN the System SHALL show the group name, rejection date, status badge, and action buttons
4. THE System SHALL sort requests with pending requests first, then rejected requests by date descending

### Requirement 4

**User Story:** As a user, I want to resend or delete my rejected join requests, so that I can retry joining a group or clean up my request history.

#### Acceptance Criteria

1. WHEN a user views a rejected join request THEN the System SHALL display "Resend" and "Delete" buttons
2. WHEN a user clicks "Resend" on a rejected request THEN the System SHALL update the request status to 'pending' and update the requested_at timestamp
3. WHEN a user clicks "Delete" on a rejected request THEN the System SHALL permanently delete the GroupMembership record
4. WHEN a user clicks "Delete" THEN the System SHALL prompt for confirmation with message "Are you sure you want to delete this request?"
5. THE System SHALL not display "Resend" or "Delete" buttons for pending requests

### Requirement 5

**User Story:** As a user, I want to view and manage invitations I've received, so that I can accept or reject group membership offers.

#### Acceptance Criteria

1. WHEN a user is on the "Join" tab THEN the System SHALL display an "Invitations" section showing all invitations with status='pending' or status='rejected'
2. WHEN displaying a pending invitation THEN the System SHALL show the group name, invited date, and "Accept" and "Reject" buttons
3. WHEN a user clicks "Accept" on a pending invitation THEN the System SHALL update status='confirmed' and set confirmed_at timestamp
4. WHEN a user clicks "Reject" on a pending invitation THEN the System SHALL update status='rejected' and set rejected_at timestamp
5. WHEN displaying a rejected invitation THEN the System SHALL show the group name, rejection date, and status badge
6. THE System SHALL not allow users to resend or delete rejected invitations (only admins can resend)

### Requirement 6

**User Story:** As an admin, I want to invite users to my group by user ID with validation, so that I can build my group membership accurately.

#### Acceptance Criteria

1. WHEN an admin is on the group members page THEN the System SHALL display an "+ Invite Member" button
2. WHEN an admin clicks "+ Invite Member" THEN the System SHALL display a modal with input fields for username, email, or user_id
3. WHEN an admin submits an invitation with a valid user identifier THEN the System SHALL create a GroupMembership with membership_type='invitation' and status='pending'
4. WHEN an admin attempts to invite a non-existent user THEN the System SHALL display an error message "User not found"
5. WHEN an admin attempts to invite a user who is already a confirmed member THEN the System SHALL display an error message "User is already a member"
6. WHEN an admin attempts to invite a user with a pending invitation THEN the System SHALL display an error message "User already has a pending invitation"
7. THE System SHALL validate that at least one user identifier field is provided before allowing submission

### Requirement 7

**User Story:** As an admin, I want to view and manage join requests for my group, so that I can approve or reject membership applications.

#### Acceptance Criteria

1. WHEN an admin views the group members page THEN the System SHALL display a "Join Requests" section showing all requests with membership_type='request' and status='pending'
2. WHEN displaying a pending join request THEN the System SHALL show the username, request date, and "Approve" and "Reject" buttons
3. WHEN an admin clicks "Approve" on a join request THEN the System SHALL update status='confirmed' and set confirmed_at timestamp
4. WHEN an admin clicks "Reject" on a join request THEN the System SHALL update status='rejected' and set rejected_at timestamp
5. THE System SHALL display the count of pending join requests in the section header

### Requirement 8

**User Story:** As an admin, I want to view rejected invitations and resend or delete them, so that I can manage invitation history and retry inviting users.

#### Acceptance Criteria

1. WHEN an admin views the group members page THEN the System SHALL display a "Rejected Invitations" section showing invitations with membership_type='invitation' and status='rejected'
2. WHEN displaying a rejected invitation THEN the System SHALL show the username, rejection date, and "Resend" and "Delete" buttons
3. WHEN an admin clicks "Resend" on a rejected invitation THEN the System SHALL update status='pending' and update invited_at timestamp
4. WHEN an admin clicks "Delete" on a rejected invitation THEN the System SHALL permanently delete the GroupMembership record
5. WHEN an admin clicks "Delete" THEN the System SHALL prompt for confirmation with message "Are you sure you want to delete this invitation?"

### Requirement 9

**User Story:** As an admin, I want to view rejected join requests and delete them, so that I can manage my group's request history.

#### Acceptance Criteria

1. WHEN an admin views the group members page THEN the System SHALL display a "Rejected Requests" section showing requests with membership_type='request' and status='rejected'
2. WHEN displaying a rejected request THEN the System SHALL show the username, rejection date, and "Delete" button
3. WHEN an admin clicks "Delete" on a rejected request THEN the System SHALL permanently delete the GroupMembership record
4. WHEN an admin clicks "Delete" THEN the System SHALL prompt for confirmation
5. THE System SHALL not allow admins to resend rejected requests (only users can resend their own requests)

### Requirement 10

**User Story:** As a system, I want to maintain data integrity for group memberships, so that the invitation and request system operates reliably.

#### Acceptance Criteria

1. THE System SHALL enforce a unique constraint on (group_id, user_id) in the GroupMembership table
2. WHEN a membership record is created THEN the System SHALL require membership_type to be either 'invitation' or 'request'
3. WHEN a membership record is created THEN the System SHALL require status to be 'pending', 'confirmed', or 'rejected'
4. WHEN status is updated to 'confirmed' THEN the System SHALL set confirmed_at to the current timestamp
5. WHEN status is updated to 'rejected' THEN the System SHALL set rejected_at to the current timestamp
6. THE System SHALL prevent users from having multiple pending or rejected memberships for the same group
7. THE System SHALL allow only one confirmed membership per user per group

### Requirement 11

**User Story:** As a system, I want to provide clear feedback for all membership actions, so that users and admins understand the results of their operations.

#### Acceptance Criteria

1. WHEN a join request is successfully created THEN the System SHALL display a success message "Join request sent successfully"
2. WHEN an invitation is successfully sent THEN the System SHALL display a success message "Invitation sent successfully"
3. WHEN a request or invitation is approved THEN the System SHALL display a success message "Request approved" or "Invitation accepted"
4. WHEN a request or invitation is rejected THEN the System SHALL display a success message "Request rejected" or "Invitation declined"
5. WHEN a resend operation succeeds THEN the System SHALL display a success message "Request resent" or "Invitation resent"
6. WHEN a delete operation succeeds THEN the System SHALL display a success message "Record deleted successfully"
7. WHEN any operation fails THEN the System SHALL display a specific error message describing the failure reason

### Requirement 12

**User Story:** As a user or admin, I want the UI to be mobile-responsive, so that I can manage group memberships on any device.

#### Acceptance Criteria

1. WHEN viewing the groups page on mobile THEN the System SHALL display tabs in a horizontally scrollable layout
2. WHEN viewing membership lists on mobile THEN the System SHALL stack action buttons vertically for better touch targets
3. THE System SHALL ensure all touch targets are minimum 44x44 pixels
4. THE System SHALL adapt layouts for screen widths below 768px
5. THE System SHALL maintain functionality across all screen sizes
