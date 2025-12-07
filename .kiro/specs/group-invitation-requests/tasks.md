# Implementation Plan

- [x] 1. Database migration and model enhancement
  - [x] 1.1 Create database migration for new fields
    - Add `membership_type` VARCHAR(20) field with choices 'invitation' or 'request'
    - Add `status` VARCHAR(20) field with choices 'pending', 'confirmed', or 'rejected'
    - Add `rejected_at` TIMESTAMP field (nullable)
    - Set default values for new fields
    - _Requirements: 10.2, 10.3_
  
  - [x] 1.2 Migrate existing data
    - Set all existing records to membership_type='invitation'
    - Set status='confirmed' where is_confirmed=TRUE
    - Set status='pending' where is_confirmed=FALSE
    - _Requirements: 10.1_
  
  - [x] 1.3 Update GroupMembership model
    - Add MEMBERSHIP_TYPE_CHOICES and STATUS_CHOICES
    - Add membership_type, status, and rejected_at fields to model
    - Update Meta indexes to include new fields
    - _Requirements: 10.2, 10.3_
  
  - [x] 1.4 Write property test for model constraints
    - **Property 8: Unique membership constraint**
    - **Validates: Requirements 10.1, 10.7**

- [x] 2. Update serializers for enhanced membership
  - [x] 2.1 Enhance GroupMembershipSerializer
    - Add membership_type, status, rejected_at to fields
    - Add group_name as read-only field
    - Update read_only_fields list
    - _Requirements: 10.2, 10.3, 10.5_
  
  - [x] 2.2 Create JoinRequestSerializer
    - Add group_name field with validation
    - Implement validate_group_name method
    - Check group exists, user not member, no pending request
    - _Requirements: 2.1, 2.3, 2.4, 2.5_
  
  - [x] 2.3 Enhance MembershipActionSerializer
    - Add 'resend' and 'delete' to action choices
    - Keep existing 'accept', 'reject', 'approve', 'decline' actions
    - _Requirements: 4.1, 8.2_
  
  - [x] 2.4 Write property tests for serializer validation
    - **Property 12: Validation prevents invalid users**
    - **Property 13: Validation prevents duplicate members**
    - **Validates: Requirements 2.3, 2.4, 6.4, 6.5**

- [x] 3. Implement join request endpoints
  - [x] 3.1 Create join request endpoint
    - POST /api/v1/groups/join-request/
    - Validate group name and user eligibility
    - Create GroupMembership with type='request', status='pending'
    - Return success message
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 3.2 Write property test for join request creation
    - **Property 1: Join request creation**
    - **Property 2: Duplicate request prevention**
    - **Validates: Requirements 2.2, 2.5, 10.6**
  
  - [x] 3.3 List user's join requests endpoint
    - GET /api/v1/groups/my-requests/
    - Filter by current user and membership_type='request'
    - Return pending and rejected requests
    - Sort by status (pending first) then date
    - _Requirements: 3.1, 3.4_
  
  - [x] 3.4 Write property test for request visibility
    - **Property 9: User request visibility**
    - **Validates: Requirements 3.1**
  
  - [x] 3.5 Manage own join request endpoint
    - PATCH /api/v1/groups/my-requests/:id/
    - Support 'resend' and 'delete' actions
    - Validate user owns the request
    - Update status or delete record
    - _Requirements: 4.2, 4.3, 4.4_
  
  - [x] 3.6 Write property tests for request management
    - **Property 6: Resend updates status**
    - **Property 7: Delete removes record**
    - **Validates: Requirements 4.2, 4.3**

- [x] 4. Implement invitation management endpoints
  - [x] 4.1 List user's invitations endpoint
    - GET /api/v1/groups/my-invitations/
    - Filter by current user and membership_type='invitation'
    - Return pending and rejected invitations
    - _Requirements: 5.1_
  
  - [x] 4.2 Write property test for invitation visibility
    - **Property 10: User invitation visibility**
    - **Validates: Requirements 5.1**
  
  - [x] 4.3 Manage received invitation endpoint
    - PATCH /api/v1/groups/my-invitations/:id/
    - Support 'accept' and 'reject' actions
    - Update status and timestamps
    - _Requirements: 5.3, 5.4_
  
  - [x] 4.4 Write property tests for invitation actions
    - **Property 4: Status transition to confirmed**
    - **Property 5: Status transition to rejected**
    - **Validates: Requirements 5.3, 5.4, 10.4, 10.5**
  
  - [x] 4.5 Update existing invite endpoint
    - Modify POST /api/v1/groups/:id/members/
    - Set membership_type='invitation' when creating
    - Keep existing validation logic
    - _Requirements: 6.3_
  
  - [x] 4.6 Write property test for invitation creation
    - **Property 3: Invitation creation with type**
    - **Validates: Requirements 6.3**

- [x] 5. Implement admin request management endpoints
  - [x] 5.1 List group join requests endpoint
    - GET /api/v1/groups/:id/join-requests/
    - Filter by group, type='request', status='pending'
    - Verify user is admin
    - Return list with count
    - _Requirements: 7.1, 7.5_
  
  - [x] 5.2 Write property test for admin request visibility
    - **Property 11: Admin request visibility**
    - **Validates: Requirements 7.1**
  
  - [x] 5.3 Manage join request endpoint
    - PATCH /api/v1/groups/:id/join-requests/:requestId/
    - Support 'approve' and 'reject' actions
    - Verify admin permissions
    - Update status and timestamps
    - _Requirements: 7.3, 7.4_
  
  - [x] 5.4 List rejected invitations endpoint
    - GET /api/v1/groups/:id/rejected-invitations/
    - Filter by group, type='invitation', status='rejected'
    - Verify admin permissions
    - _Requirements: 8.1_
  
  - [x] 5.5 Manage rejected invitation endpoint
    - PATCH /api/v1/groups/:id/rejected-invitations/:id/
    - Support 'resend' and 'delete' actions
    - Verify admin permissions
    - _Requirements: 8.3, 8.4, 8.5_
  
  - [x] 5.6 List rejected requests endpoint
    - GET /api/v1/groups/:id/rejected-requests/
    - Filter by group, type='request', status='rejected'
    - Verify admin permissions
    - _Requirements: 9.1_
  
  - [x] 5.7 Manage rejected request endpoint
    - PATCH /api/v1/groups/:id/rejected-requests/:id/
    - Support 'delete' action only
    - Verify admin permissions
    - _Requirements: 9.3, 9.4_

- [x] 6. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update frontend API service layer
  - [x] 7.1 Add join request API methods
    - createJoinRequest(groupName)
    - listMyRequests()
    - manageMyRequest(requestId, action)
    - _Requirements: 2.2, 3.1, 4.2, 4.3_
  
  - [x] 7.2 Add invitation API methods
    - listMyInvitations()
    - manageMyInvitation(invitationId, action)
    - _Requirements: 5.1, 5.3, 5.4_
  
  - [x] 7.3 Add admin management API methods
    - listGroupJoinRequests(groupId)
    - manageJoinRequest(groupId, requestId, action)
    - listRejectedInvitations(groupId)
    - manageRejectedInvitation(groupId, invitationId, action)
    - listRejectedRequests(groupId)
    - manageRejectedRequest(groupId, requestId, action)
    - _Requirements: 7.1, 7.3, 8.1, 8.3, 9.1, 9.3_

- [x] 8. Implement Groups page tab structure
  - [x] 8.1 Create Tabs component
    - Build reusable Tabs component with Tab children
    - Support default tab selection
    - Handle tab switching
    - Mobile-responsive horizontal scroll
    - _Requirements: 1.1, 12.1_
  
  - [x] 8.2 Restructure GroupsPage with tabs
    - Add Tabs wrapper with "Join" and "Create" tabs
    - Set "Join" as default first tab
    - Move CreateGroupForm to "Create" tab
    - _Requirements: 1.2, 1.3, 1.4, 1.5_
  
  - [x] 8.3 Write property test for tab display
    - **Property 14: Tab display order**
    - **Validates: Requirements 1.2, 1.3**

- [x] 9. Implement Join tab components
  - [x] 9.1 Create JoinRequestForm component
    - Input field for group name
    - "Request to Join" button
    - Form validation
    - Success/error message display
    - _Requirements: 2.1, 2.6, 11.1_
  
  - [x] 9.2 Create MyJoinRequestsList component
    - Display pending and rejected requests
    - Show group name, date, status badge
    - Action buttons for rejected requests (Resend, Delete)
    - Confirmation dialog for delete
    - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.4_
  
  - [x] 9.3 Create MyInvitationsList component
    - Display pending and rejected invitations
    - Show group name, date, status badge
    - Action buttons for pending (Accept, Reject)
    - No actions for rejected invitations
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [x] 9.4 Create JoinTab component
    - Combine JoinRequestForm and lists
    - Section headers and layout
    - Handle all user actions
    - Display feedback messages
    - _Requirements: 1.4, 11.1-11.7_

- [x] 10. Implement admin management components
  - [x] 10.1 Create JoinRequestsList component
    - Display pending join requests
    - Show username, request date
    - Approve and Reject buttons
    - Request count in header
    - _Requirements: 7.1, 7.2, 7.5_
  
  - [x] 10.2 Create RejectedInvitationsList component
    - Display rejected invitations
    - Show username, rejection date
    - Resend and Delete buttons
    - Confirmation dialogs
    - _Requirements: 8.1, 8.2, 8.5_
  
  - [x] 10.3 Create RejectedRequestsList component
    - Display rejected requests
    - Show username, rejection date
    - Delete button only
    - Confirmation dialog
    - _Requirements: 9.1, 9.2, 9.4_
  
  - [x] 10.4 Update GroupDetailPage members tab
    - Add JoinRequestsList section
    - Add RejectedInvitationsList section
    - Add RejectedRequestsList section
    - Update layout and styling
    - _Requirements: 7.1, 8.1, 9.1_
  
  - [x] 10.5 Write property test for action button visibility
    - **Property 15: Action button visibility**
    - **Validates: Requirements 4.1, 8.2, 9.2**

- [x] 11. Implement mobile-responsive styling
  - [x] 11.1 Style Tabs component for mobile
    - Horizontal scrollable tabs on mobile
    - Touch-friendly tab buttons (44x44px min)
    - Responsive breakpoints
    - _Requirements: 12.1, 12.3, 12.4_
  
  - [x] 11.2 Style Join tab components for mobile
    - Full-width form inputs
    - Stacked action buttons on mobile
    - Card-based layout for lists
    - _Requirements: 12.2, 12.3, 12.5_
  
  - [x] 11.3 Style admin management components for mobile
    - Responsive section layouts
    - Touch-friendly action buttons
    - Collapsible sections on mobile
    - _Requirements: 12.2, 12.3, 12.5_

- [x] 12. Implement user feedback and error handling
  - [x] 12.1 Add success messages
    - Toast notifications for all successful actions
    - Specific messages per action type
    - Auto-dismiss after 3 seconds
    - _Requirements: 11.1-11.6_
  
  - [x] 12.2 Add error handling
    - Display validation errors inline
    - Show API error messages
    - Specific error messages for each failure type
    - _Requirements: 11.7_
  
  - [x] 12.3 Add loading states
    - Loading indicators for async operations
    - Disable buttons during processing
    - Skeleton loaders for lists
    - _Requirements: 11.1-11.7_

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Integration testing and bug fixes
  - [x] 14.1 Test complete user join request flow
    - User requests to join group
    - Admin approves request
    - User becomes confirmed member
    - _Requirements: All_
  
  - [x] 14.2 Test complete invitation flow
    - Admin invites user
    - User accepts invitation
    - User becomes confirmed member
    - _Requirements: All_
  
  - [x] 14.3 Test rejection and resend flows
    - User requests, admin rejects, user resends
    - Admin invites, user rejects, admin resends
    - _Requirements: 4.2, 8.3_
  
  - [x] 14.4 Test delete operations
    - User deletes own rejected request
    - Admin deletes rejected invitation
    - Admin deletes rejected request
    - _Requirements: 4.3, 8.4, 9.3_
  
  - [x] 14.5 Test validation and error cases
    - Invalid group names
    - Duplicate requests
    - Already member scenarios
    - Permission errors
    - _Requirements: 2.3, 2.4, 2.5, 6.4, 6.5, 6.6_

- [x] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
