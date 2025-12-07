# Design Document

## Overview

This design document specifies the enhanced group invitation and join request system for Sententiam Ferre. The system extends the existing admin-initiated invitation flow with bidirectional membership management, allowing users to request to join groups and providing comprehensive management tools for both invitations and requests.

### Key Design Principles

1. **Bidirectional Flow**: Support both admin→user invitations and user→admin join requests
2. **State Preservation**: Maintain rejection history to enable resend functionality
3. **Clear Separation**: Distinguish between invitation and request types in data model
4. **User Experience**: Provide intuitive UI with clear feedback and status indicators
5. **Data Integrity**: Enforce constraints while allowing flexible state transitions

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Groups Page  │  │ Join Tab     │  │ Create Tab   │      │
│  │ with Tabs    │  │ Component    │  │ Component    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Invitations  │  │ Join         │  │ Admin        │      │
│  │ List         │  │ Requests     │  │ Management   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTPS/REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Django Rest Framework                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Group        │  │ Membership   │  │ Request      │      │
│  │ ViewSet      │  │ ViewSet      │  │ ViewSet      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ app_group    │  │group_        │                         │
│  │              │  │membership    │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                               │
│  New Fields: membership_type, status, rejected_at           │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. Enhanced GroupMembership Model

**New Fields:**
- `membership_type`: ENUM('invitation', 'request') - Indicates who initiated
- `status`: ENUM('pending', 'confirmed', 'rejected') - Current state
- `rejected_at`: TIMESTAMP - When rejection occurred
- `requested_at`: TIMESTAMP - For join requests (replaces invited_at semantically)

**Field Mapping:**
- `invited_at` → Used for both invitations and requests (creation timestamp)
- `confirmed_at` → Set when status becomes 'confirmed'
- `rejected_at` → Set when status becomes 'rejected'

**State Machine:**
```
pending → confirmed (accept/approve)
pending → rejected (reject/decline)
rejected → pending (resend)
rejected → deleted (delete)
```

#### 2. API Endpoints

**New Endpoints:**
```
POST   /api/v1/groups/join-request/          # User creates join request
GET    /api/v1/groups/my-requests/           # User's join requests
PATCH  /api/v1/groups/my-requests/:id/       # Resend/delete own request
GET    /api/v1/groups/my-invitations/        # User's received invitations
PATCH  /api/v1/groups/my-invitations/:id/    # Accept/reject invitation

GET    /api/v1/groups/:id/join-requests/     # Admin views pending requests
PATCH  /api/v1/groups/:id/join-requests/:id/ # Admin approve/reject request
GET    /api/v1/groups/:id/rejected-invitations/ # Admin views rejected invitations
GET    /api/v1/groups/:id/rejected-requests/    # Admin views rejected requests
```

**Modified Endpoints:**
```
POST   /api/v1/groups/:id/members/           # Now creates invitation type
PATCH  /api/v1/groups/:id/members/:userId/   # Enhanced with resend capability
```

#### 3. Serializers

**GroupMembershipSerializer** (Enhanced):
```python
class GroupMembershipSerializer(serializers.ModelSerializer):
    user = UserAccountSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = GroupMembership
        fields = [
            'id', 'group', 'group_name', 'user', 'user_id', 
            'role', 'membership_type', 'status',
            'invited_at', 'confirmed_at', 'rejected_at'
        ]
        read_only_fields = ['id', 'invited_at', 'confirmed_at', 'rejected_at']
```

**JoinRequestSerializer** (New):
```python
class JoinRequestSerializer(serializers.Serializer):
    group_name = serializers.CharField(required=True)
    
    def validate_group_name(self, value):
        # Validate group exists
        # Validate user not already member
        # Validate no pending request exists
```

**MembershipActionSerializer** (Enhanced):
```python
class MembershipActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=['accept', 'reject', 'approve', 'decline', 'resend', 'delete']
    )
```

### Frontend Components

#### 1. Groups Page Restructure

**GroupsPage Component** (Modified):
```jsx
<div className="groups-page">
  <Tabs>
    <Tab label="Join" default>
      <JoinTab />
    </Tab>
    <Tab label="Create">
      <CreateGroupForm />
    </Tab>
  </Tabs>
</div>
```

#### 2. Join Tab Component (New)

**JoinTab Component**:
```jsx
<div className="join-tab">
  <section className="join-requests-section">
    <h2>Request to Join</h2>
    <JoinRequestForm onSubmit={handleJoinRequest} />
    <MyJoinRequestsList requests={myRequests} />
  </section>
  
  <section className="invitations-section">
    <h2>Invitations</h2>
    <MyInvitationsList invitations={myInvitations} />
  </section>
</div>
```

**Components:**
- `JoinRequestForm`: Input for group name + Request button
- `MyJoinRequestsList`: Shows pending and rejected requests with actions
- `MyInvitationsList`: Shows pending and rejected invitations with actions

#### 3. Admin Management Components (Enhanced)

**GroupDetailPage** (Modified):
```jsx
<div className="members-tab">
  <section className="confirmed-members">
    <h2>Members</h2>
    <MembersList members={confirmedMembers} />
  </section>
  
  <section className="pending-invitations">
    <h2>Pending Invitations</h2>
    <PendingInvitationsList invitations={pendingInvitations} />
  </section>
  
  <section className="join-requests">
    <h2>Join Requests ({pendingRequests.length})</h2>
    <JoinRequestsList 
      requests={pendingRequests} 
      onApprove={handleApprove}
      onReject={handleReject}
    />
  </section>
  
  <section className="rejected-invitations">
    <h2>Rejected Invitations</h2>
    <RejectedInvitationsList 
      invitations={rejectedInvitations}
      onResend={handleResend}
      onDelete={handleDelete}
    />
  </section>
  
  <section className="rejected-requests">
    <h2>Rejected Requests</h2>
    <RejectedRequestsList 
      requests={rejectedRequests}
      onDelete={handleDelete}
    />
  </section>
</div>
```

## Data Models

### Enhanced GroupMembership Model

```python
class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]
    
    MEMBERSHIP_TYPE_CHOICES = [
        ('invitation', 'Invitation'),  # Admin invited user
        ('request', 'Request'),        # User requested to join
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(AppGroup, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='member')
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_at = models.DateTimeField(auto_now_add=True)  # Creation timestamp
    confirmed_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'group_membership'
        unique_together = [['group', 'user']]
        indexes = [
            models.Index(fields=['group', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['membership_type', 'status']),
        ]
```

### State Transitions

**Valid Transitions:**
```
pending → confirmed:
  - User accepts invitation
  - Admin approves request
  - Sets confirmed_at timestamp

pending → rejected:
  - User rejects invitation
  - Admin rejects request
  - Sets rejected_at timestamp

rejected → pending:
  - User resends rejected request
  - Admin resends rejected invitation
  - Updates invited_at timestamp
  - Clears rejected_at

rejected → deleted:
  - User deletes own rejected request
  - Admin deletes rejected invitation/request
  - Permanently removes record
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Join request creation
*For any* user and valid group name, creating a join request should result in a GroupMembership record with membership_type='request' and status='pending'.
**Validates: Requirements 2.2**

### Property 2: Duplicate request prevention
*For any* user and group combination, attempting to create a join request when a pending or rejected request already exists should be rejected.
**Validates: Requirements 2.5, 10.6**

### Property 3: Invitation creation with type
*For any* admin invitation, the created GroupMembership should have membership_type='invitation' and status='pending'.
**Validates: Requirements 6.3**

### Property 4: Status transition to confirmed
*For any* pending membership (invitation or request), accepting/approving it should update status='confirmed' and set confirmed_at timestamp.
**Validates: Requirements 5.3, 7.3, 10.4**

### Property 5: Status transition to rejected
*For any* pending membership, rejecting/declining it should update status='rejected' and set rejected_at timestamp.
**Validates: Requirements 5.4, 7.4, 10.5**

### Property 6: Resend updates status
*For any* rejected membership, resending should update status='pending', update invited_at, and clear rejected_at.
**Validates: Requirements 4.2, 8.3**

### Property 7: Delete removes record
*For any* rejected membership, deleting should permanently remove the GroupMembership record from the database.
**Validates: Requirements 4.3, 8.4, 9.3**

### Property 8: Unique membership constraint
*For any* group and user combination, only one GroupMembership record should exist at any time.
**Validates: Requirements 10.1, 10.7**

### Property 9: User request visibility
*For any* user, querying their join requests should return only memberships where user matches and membership_type='request'.
**Validates: Requirements 3.1**

### Property 10: User invitation visibility
*For any* user, querying their invitations should return only memberships where user matches and membership_type='invitation'.
**Validates: Requirements 5.1**

### Property 11: Admin request visibility
*For any* group admin, querying join requests should return only memberships where group matches, membership_type='request', and status='pending'.
**Validates: Requirements 7.1**

### Property 12: Validation prevents invalid users
*For any* invitation or join request, attempting to use a non-existent user or group should be rejected with appropriate error message.
**Validates: Requirements 2.3, 6.4**

### Property 13: Validation prevents duplicate members
*For any* invitation or join request, attempting to add a user who is already a confirmed member should be rejected.
**Validates: Requirements 2.4, 6.5**

### Property 14: Tab display order
*For any* groups page load, the "Join" tab should be displayed first and the "Create" tab second.
**Validates: Requirements 1.2, 1.3**

### Property 15: Action button visibility
*For any* rejected membership, the appropriate action buttons (Resend/Delete) should be displayed based on membership_type and user role.
**Validates: Requirements 4.1, 8.2, 9.2**

## Error Handling

### Validation Errors
- **Group Not Found**: Return 404 with message "Group not found"
- **User Not Found**: Return 404 with message "User not found"
- **Already Member**: Return 400 with message "User is already a member"
- **Pending Request Exists**: Return 400 with message "Pending request already exists"
- **Invalid Action**: Return 400 with message describing valid actions

### Authorization Errors
- **Not Admin**: Return 403 when non-admin attempts admin actions
- **Not Owner**: Return 403 when user attempts to modify another user's request
- **Invalid Group Access**: Return 403 when accessing group without membership

### State Transition Errors
- **Invalid Transition**: Return 400 when attempting invalid state change
- **Already Processed**: Return 400 when acting on already-processed membership

## Testing Strategy

### Unit Testing

**Model Tests:**
- Test GroupMembership creation with different types
- Test status transitions
- Test unique constraints
- Test timestamp updates

**Serializer Tests:**
- Test JoinRequestSerializer validation
- Test MembershipActionSerializer with all actions
- Test error messages for invalid data

**View Tests:**
- Test join request creation endpoint
- Test invitation management endpoints
- Test admin approval/rejection endpoints
- Test resend and delete operations

### Property-Based Testing

Using **Hypothesis** for Python property tests (minimum 100 iterations):

**Property Test Coverage:**
- Join request creation and validation (Properties 1-2)
- Invitation creation (Property 3)
- Status transitions (Properties 4-5)
- Resend and delete operations (Properties 6-7)
- Uniqueness constraints (Property 8)
- Visibility and filtering (Properties 9-11)
- Validation rules (Properties 12-13)

**Test Tagging Format:**
```python
# Feature: group-invitation-requests, Property 1: Join request creation
```

### Integration Testing

**End-to-End Flows:**
1. User requests to join → Admin approves → User becomes member
2. Admin invites user → User accepts → User becomes member
3. User requests to join → Admin rejects → User resends → Admin approves
4. Admin invites user → User rejects → Admin resends → User accepts
5. User requests to join → User deletes request
6. Admin invites user → User rejects → Admin deletes invitation

## Mobile-First UI Design

### Responsive Breakpoints
- **Mobile**: < 768px (primary target)
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Touch Optimizations
- Minimum touch target: 44x44px
- Tab navigation: Horizontal scroll on mobile
- Action buttons: Stack vertically on mobile
- Forms: Full-width inputs on mobile

### UI Components

**Tab Navigation:**
```
Mobile:
┌─────────────────────────────┐
│ [Join] [Create]             │
└─────────────────────────────┘

Desktop:
┌─────────────────────────────┐
│  Join  │  Create             │
└─────────────────────────────┘
```

**Join Request Form:**
```
┌─────────────────────────────┐
│ Request to Join a Group     │
│ ┌─────────────────────────┐ │
│ │ Enter group name...     │ │
│ └─────────────────────────┘ │
│ [Request to Join]           │
└─────────────────────────────┘
```

**Request/Invitation Card:**
```
┌─────────────────────────────┐
│ Group Name                  │
│ Status: Pending             │
│ Requested: 2 days ago       │
│ [Accept] [Reject]           │
└─────────────────────────────┘
```

## Security Considerations

### Authorization
- Only admins can approve/reject join requests
- Only admins can resend/delete invitations
- Users can only manage their own requests
- Users can only view invitations sent to them

### Validation
- Validate group existence before creating requests
- Validate user existence before creating invitations
- Prevent duplicate memberships
- Sanitize all user inputs

### Data Privacy
- Users cannot see other users' requests
- Admins can only see requests for their groups
- Membership history is private to involved parties

## Migration Strategy

### Database Migration

**Step 1: Add New Fields**
```sql
ALTER TABLE group_membership 
ADD COLUMN membership_type VARCHAR(20) DEFAULT 'invitation',
ADD COLUMN status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN rejected_at TIMESTAMP NULL;
```

**Step 2: Migrate Existing Data**
```sql
-- Set existing records as invitations
UPDATE group_membership 
SET membership_type = 'invitation';

-- Set confirmed members
UPDATE group_membership 
SET status = 'confirmed' 
WHERE is_confirmed = TRUE;

-- Set pending invitations
UPDATE group_membership 
SET status = 'pending' 
WHERE is_confirmed = FALSE;
```

**Step 3: Add Constraints**
```sql
ALTER TABLE group_membership
ALTER COLUMN membership_type SET NOT NULL,
ALTER COLUMN status SET NOT NULL;

CREATE INDEX idx_membership_type_status 
ON group_membership(membership_type, status);
```

### Backward Compatibility

- Keep `is_confirmed` field temporarily for rollback
- Maintain existing API endpoints during transition
- Add new endpoints without breaking old ones
- Deprecate old endpoints after migration complete

## Future Enhancements

### Phase 2 Features
- **Group Discovery**: Browse public groups
- **Search Functionality**: Search groups by name/description
- **Invitation Links**: Generate shareable invitation URLs
- **Bulk Actions**: Approve/reject multiple requests at once
- **Notifications**: Real-time alerts for new requests/invitations
- **Request Messages**: Allow users to include a message with requests

### Phase 3 Features
- **Group Categories**: Organize groups by category
- **Member Limits**: Set maximum group size
- **Auto-Approval Rules**: Automatically approve requests based on criteria
- **Invitation Expiry**: Set expiration dates for invitations
- **Request History**: Full audit trail of all membership actions
