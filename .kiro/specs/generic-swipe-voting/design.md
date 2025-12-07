# Design Document

## Overview

Sententiam Ferre is a mobile-first collaborative decision-making platform built with Django Rest Framework (DRF) backend and React JavaScript frontend. The system enables groups to reach consensus through swipe-style voting, with real-time favourite detection based on configurable approval rules. The architecture emphasizes mobile responsiveness, real-time updates, and scalable data modeling using PostgreSQL with JSONB for flexible item attributes.

### Key Design Principles

1. **Mobile-First**: Swipe-based UI optimized for touch interactions
2. **Real-Time Consensus**: Database triggers automatically detect when items meet approval thresholds
3. **Flexible Data Model**: JSONB attributes support diverse item types without schema migrations
4. **Privacy-Focused**: Role-based access control ensures group data isolation
5. **Scalable**: Indexed queries and pagination support large item sets

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile/Web Client                        │
│                   (React JavaScript)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Swipe Cards  │  │ Chat View    │  │ Favourites   │      │
│  │ Component    │  │ Component    │  │ List         │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTPS/REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Django Rest Framework                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth         │  │ Groups       │  │ Decisions    │      │
│  │ ViewSets     │  │ ViewSets     │  │ ViewSets     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Voting       │  │ Chat         │  │ Taxonomies   │      │
│  │ ViewSets     │  │ ViewSets     │  │ ViewSets     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Django ORM / Business Logic               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ user_account │  │ app_group    │  │ decision     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │decision_item │  │decision_vote │  │decision_     │      │
│  │              │  │              │  │selection     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Trigger: trg_maybe_select_item                     │    │
│  │  (Auto-evaluates approval rules on vote changes)    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Django 5.2 LTS with Django Rest Framework
- Python package management via UV (https://docs.astral.sh/uv/)
- pyproject.toml as single source of truth for dependencies
- PostgreSQL 14+ (JSONB support, triggers)
- Django Channels (optional for WebSocket chat)
- Argon2 for password hashing

**Frontend:**
- React 18 (latest stable, JavaScript, no TypeScript)
- React Router for navigation
- Axios for API calls
- CSS Modules or Styled Components for styling
- React Swipeable or similar for swipe gestures

**Infrastructure:**
- RESTful API design
- Token-based authentication (JWT or DRF tokens)
- CORS configuration for frontend-backend communication

**Development Workflow:**
- All Python commands MUST be run using UV (e.g., `uv run python`, `uv run django-admin`)
- All Python dependencies MUST be added to pyproject.toml
- All dependency installations MUST use `uv sync` or `uv add <package>`
- Never use pip directly; always use UV for package management

## Components and Interfaces

### Backend Components

#### 1. Authentication Module

**Models:**
- `UserAccount`: Custom user model extending Django's AbstractUser

**ViewSets:**
- `AuthViewSet`: Handles signup, login, logout, token refresh

**Endpoints:**
- `POST /api/v1/auth/signup`: Create new user account
- `POST /api/v1/auth/login`: Authenticate and return token
- `POST /api/v1/auth/logout`: Invalidate token
- `GET /api/v1/auth/me`: Get current user profile

#### 2. Group Management Module

**Models:**
- `AppGroup`: Group entity with name, description, created_at
- `GroupMembership`: Links users to groups with role and confirmation status

**ViewSets:**
- `GroupViewSet`: CRUD operations for groups
- `GroupMembershipViewSet`: Manage invitations and memberships

**Endpoints:**
- `POST /api/v1/groups`: Create group
- `GET /api/v1/groups/:id`: Get group details
- `GET /api/v1/groups/:id/members`: List members
- `POST /api/v1/groups/:id/members`: Invite user
- `PATCH /api/v1/groups/:id/members/:userId`: Accept/decline invitation
- `DELETE /api/v1/groups/:id/members/:userId`: Remove member

#### 3. Decision Module

**Models:**
- `Decision`: Decision entity with title, description, item_type, rules (JSONField), status
- `DecisionSharedGroup`: Many-to-many for cross-group decisions

**ViewSets:**
- `DecisionViewSet`: CRUD operations for decisions

**Endpoints:**
- `POST /api/v1/decisions`: Create decision
- `GET /api/v1/decisions/:id`: Get decision details
- `PATCH /api/v1/decisions/:id`: Update decision (status, rules)
- `POST /api/v1/decisions/:id/share-group`: Share with another group
- `GET /api/v1/decisions/:id/favourites`: Get items in decision_selection

#### 4. Item Module

**Models:**
- `DecisionItem`: Item with label, attributes (JSONField), optional catalog_item_id
- `CatalogItem`: Reusable item templates (optional)
- `DecisionItemTerm`: Links items to taxonomy terms

**ViewSets:**
- `DecisionItemViewSet`: CRUD operations for items within decisions

**Endpoints:**
- `POST /api/v1/decisions/:id/items`: Add item to decision
- `GET /api/v1/decisions/:id/items`: List items with filtering
- `PATCH /api/v1/items/:itemId`: Update item
- `DELETE /api/v1/items/:itemId`: Remove item
- `POST /api/v1/items/:itemId/terms/:termId`: Tag item
- `DELETE /api/v1/items/:itemId/terms/:termId`: Untag item

**Query Parameters for Item Listing:**
- `tag`: Filter by term (e.g., `category:suv`)
- Attribute filters: Dynamic based on JSONB content (e.g., `maxPrice=40000`)
- `page`, `page_size`: Pagination

#### 5. Voting Module

**Models:**
- `DecisionVote`: User vote with is_like (boolean), rating (integer), weight, note

**ViewSets:**
- `VoteViewSet`: Create and update votes

**Endpoints:**
- `POST /api/v1/items/:itemId/votes`: Cast or update vote
- `GET /api/v1/items/:itemId/votes/me`: Get current user's vote
- `GET /api/v1/items/:itemId/votes/summary`: Get aggregate vote counts

#### 6. Favourites Module

**Models:**
- `DecisionSelection`: Items that met approval rules with snapshot data

**Logic:**
- Database trigger `trg_maybe_select_item` automatically inserts records
- ViewSet provides read-only access

**Endpoints:**
- `GET /api/v1/decisions/:id/favourites`: List favourite items

#### 7. Chat Module

**Models:**
- `Conversation`: Chat thread linked to decision
- `Message`: Individual messages with sender, text, sent_at, is_read

**ViewSets:**
- `ConversationViewSet`: Get or create conversation
- `MessageViewSet`: Send and retrieve messages

**Endpoints:**
- `GET /api/v1/decisions/:id/conversation`: Get conversation
- `POST /api/v1/decisions/:id/messages`: Send message
- `GET /api/v1/decisions/:id/messages`: List messages (paginated)
- `PATCH /api/v1/messages/:messageId`: Mark as read

#### 8. Taxonomy Module

**Models:**
- `Taxonomy`: Classification system (e.g., "category", "origin")
- `Term`: Specific values with optional attributes (JSONField for UI metadata)

**ViewSets:**
- `TaxonomyViewSet`: CRUD for taxonomies
- `TermViewSet`: CRUD for terms

**Endpoints:**
- `GET /api/v1/taxonomies`: List all taxonomies
- `POST /api/v1/taxonomies`: Create taxonomy
- `POST /api/v1/taxonomies/:taxonomyId/terms`: Add term
- `GET /api/v1/taxonomies/:taxonomyId/terms`: List terms

#### 9. Questionnaire Module

**Models:**
- `Question`: Question with text, scope (global/item_type/decision/group)
- `AnswerOption`: Predefined answer choices
- `UserAnswer`: User responses with optional decision_id scope

**ViewSets:**
- `QuestionViewSet`: List questions by scope
- `UserAnswerViewSet`: Submit answers

**Endpoints:**
- `GET /api/v1/questions`: List questions (filter by scope, decision_id)
- `POST /api/v1/answers`: Submit answer

### Frontend Components

#### 1. Authentication Components

- `SignupForm`: User registration
- `LoginForm`: User authentication
- `AuthContext`: React context for auth state management

#### 2. Group Components

- `GroupList`: Display user's groups
- `GroupDetail`: Show group info and members
- `InviteModal`: Invite users to group
- `MemberList`: Display group members with status

#### 3. Decision Components

- `DecisionList`: Display decisions for a group
- `DecisionDetail`: Show decision info, rules, status
- `CreateDecisionForm`: Create new decision with rule configuration
- `RuleSelector`: UI for choosing unanimous vs threshold rules

#### 4. Swipe/Voting Components

- `SwipeCardStack`: Main swipe interface (Tinder-style)
- `ItemCard`: Individual item display with image, label, attributes
- `SwipeGestures`: Handle left/right swipe events
- `VoteButtons`: Alternative to swipe (like/dislike buttons)
- `RatingInput`: Star or numeric rating input

#### 5. Favourites Components

- `FavouritesList`: Display items that met approval rules
- `FavouriteCard`: Show favourite item with vote snapshot

#### 6. Chat Components

- `ChatView`: Message list and input
- `MessageList`: Scrollable message history
- `MessageInput`: Text input with send button
- `MessageBubble`: Individual message display

#### 7. Item Management Components

- `ItemList`: Admin view of all items in decision
- `AddItemForm`: Create new item with attributes
- `ItemFilter`: Filter by tags and attributes
- `TagSelector`: Multi-select for taxonomy terms

#### 8. Questionnaire Components

- `QuestionnaireView`: Display questions
- `QuestionCard`: Individual question with answer input
- `AnswerSubmit`: Submit answer button

### API Response Formats

**Standard Success Response:**
```json
{
  "status": "success",
  "data": { ... }
}
```

**Standard Error Response:**
```json
{
  "status": "error",
  "message": "Error description",
  "errors": { ... }
}
```

**Pagination Response:**
```json
{
  "status": "success",
  "data": {
    "results": [ ... ],
    "count": 100,
    "next": "url",
    "previous": "url"
  }
}
```

## Data Models

### Core Models

#### UserAccount
```python
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "password_hash": "string",  # Argon2
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### AppGroup
```python
{
  "id": "uuid",
  "name": "string",
  "description": "text",
  "created_by": "uuid (FK to UserAccount)",
  "created_at": "timestamp"
}
```

#### GroupMembership
```python
{
  "id": "uuid",
  "group_id": "uuid (FK to AppGroup)",
  "user_id": "uuid (FK to UserAccount)",
  "role": "string (admin/member)",
  "is_confirmed": "boolean",
  "invited_at": "timestamp",
  "confirmed_at": "timestamp"
}
```

#### Decision
```python
{
  "id": "uuid",
  "group_id": "uuid (FK to AppGroup)",
  "title": "string",
  "description": "text",
  "item_type": "string",
  "rules": "json",  # {"type": "unanimous"} or {"type": "threshold", "value": 0.7}
  "status": "string (draft/open/closed/archived)",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### DecisionItem
```python
{
  "id": "uuid",
  "decision_id": "uuid (FK to Decision)",
  "catalog_item_id": "uuid (FK to CatalogItem, nullable)",
  "label": "string",
  "attributes": "jsonb",  # Flexible attributes like {"price": 40000, "color": "red"}
  "external_ref": "string (nullable)",
  "created_at": "timestamp"
}
```

#### DecisionVote
```python
{
  "id": "uuid",
  "item_id": "uuid (FK to DecisionItem)",
  "user_id": "uuid (FK to UserAccount)",
  "is_like": "boolean (nullable)",
  "rating": "integer (nullable)",
  "weight": "decimal (default 1.0)",
  "note": "text (nullable)",
  "voted_at": "timestamp",
  # UNIQUE constraint on (user_id, item_id)
}
```

#### DecisionSelection (Favourites)
```python
{
  "id": "uuid",
  "decision_id": "uuid (FK to Decision)",
  "item_id": "uuid (FK to DecisionItem)",
  "selected_at": "timestamp",
  "snapshot": "jsonb"  # {"approvals": 5, "total_members": 7, "rule": {...}}
}
```

#### Conversation
```python
{
  "id": "uuid",
  "decision_id": "uuid (FK to Decision)",
  "created_at": "timestamp"
}
```

#### Message
```python
{
  "id": "uuid",
  "conversation_id": "uuid (FK to Conversation)",
  "sender_id": "uuid (FK to UserAccount)",
  "text": "text",
  "sent_at": "timestamp",
  "is_read": "boolean"
}
```

#### Taxonomy
```python
{
  "id": "uuid",
  "name": "string",  # e.g., "category", "origin"
  "description": "text"
}
```

#### Term
```python
{
  "id": "uuid",
  "taxonomy_id": "uuid (FK to Taxonomy)",
  "value": "string",  # e.g., "SUV", "sedan"
  "attributes": "jsonb"  # {"color": "#FF0000", "icon": "car"}
}
```

#### DecisionItemTerm
```python
{
  "id": "uuid",
  "item_id": "uuid (FK to DecisionItem)",
  "term_id": "uuid (FK to Term)"
}
```

#### Question
```python
{
  "id": "uuid",
  "text": "string",
  "scope": "string (global/item_type/decision/group)",
  "item_type": "string (nullable)",
  "created_at": "timestamp"
}
```

#### AnswerOption
```python
{
  "id": "uuid",
  "question_id": "uuid (FK to Question)",
  "text": "string",
  "order": "integer"
}
```

#### UserAnswer
```python
{
  "id": "uuid",
  "user_id": "uuid (FK to UserAccount)",
  "question_id": "uuid (FK to Question)",
  "decision_id": "uuid (FK to Decision, nullable)",
  "answer_option_id": "uuid (FK to AnswerOption, nullable)",
  "answer_value": "jsonb (nullable)",
  "answered_at": "timestamp",
  # UNIQUE constraint on (user_id, question_id, decision_id)
}
```

### Database Indexes

**Performance-Critical Indexes:**
- `decision_item.attributes`: GIN index for JSONB queries
- `decision_item_term (item_id, term_id)`: BTREE for tag filtering
- `decision_vote (user_id, item_id)`: UNIQUE index for vote constraints
- `message (conversation_id, sent_at)`: BTREE for chat pagination
- `group_membership (group_id, is_confirmed)`: BTREE for member queries
- `decision_selection (decision_id)`: BTREE for favourites lookup

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Password hashing preservation
*For any* valid user registration, the stored password_hash should never equal the plaintext password, and verifying the plaintext against the hash should succeed.
**Validates: Requirements 1.1, 12.1**

### Property 2: Authentication token validity
*For any* valid login with correct credentials, the system should return a token that can be used to authenticate subsequent requests.
**Validates: Requirements 1.2**

### Property 3: Invalid credential rejection
*For any* invalid credentials (wrong password or non-existent user), authentication should fail without revealing which part is incorrect.
**Validates: Requirements 1.3**

### Property 4: Password complexity enforcement
*For any* password that violates complexity requirements, registration should be rejected with appropriate error messages.
**Validates: Requirements 1.4**

### Property 5: Group creator auto-membership
*For any* newly created group, the creator should automatically appear as a confirmed member with appropriate role.
**Validates: Requirements 2.1**

### Property 6: Invitation creates pending membership
*For any* registered user invited to a group, a group_membership record with is_confirmed=FALSE should be created.
**Validates: Requirements 2.2**

### Property 7: Invitation acceptance updates status
*For any* pending invitation, accepting it should set is_confirmed=TRUE and preserve all other membership data.
**Validates: Requirements 2.4**

### Property 8: Invitation decline removes membership
*For any* pending invitation, declining it should remove the group_membership record entirely.
**Validates: Requirements 2.5**

### Property 9: Decision field persistence
*For any* decision creation, all provided fields (title, description, item_type, rules, status) should be retrievable unchanged.
**Validates: Requirements 3.1**

### Property 10: Threshold rule validation
*For any* threshold value between 0 and 1, creating a decision with that threshold should store the rules JSON correctly with type "threshold" and the specified value.
**Validates: Requirements 3.3**

### Property 11: Decision initial status
*For any* newly created decision without explicit status, the initial status should be "open".
**Validates: Requirements 3.4**

### Property 12: Decision status transitions
*For any* decision status update, only valid state transitions (draft→open, open→closed, closed→archived) should be allowed.
**Validates: Requirements 3.5**

### Property 13: Item attribute storage
*For any* item with JSONB attributes, storing and retrieving the item should preserve all attribute key-value pairs.
**Validates: Requirements 4.1**

### Property 14: Catalog item linking
*For any* item linked to a catalog_item, the catalog_item_id reference should be stored and retrievable.
**Validates: Requirements 4.2**

### Property 15: Item tagging creates link
*For any* item and term, tagging the item should create a decision_item_term record linking them.
**Validates: Requirements 4.3**

### Property 16: Duplicate item prevention
*For any* decision, attempting to add an item with the same external_ref and label as an existing item should be rejected.
**Validates: Requirements 4.4**

### Property 17: Vote storage and updates
*For any* vote on an item, the system should store or update a single decision_vote record with the provided is_like or rating values.
**Validates: Requirements 5.1, 5.2**

### Property 18: Vote field requirement
*For any* vote submission, at least one of is_like or rating must be provided, otherwise the vote should be rejected.
**Validates: Requirements 5.4**

### Property 19: Unanimous rule evaluation
*For any* decision with unanimous rules, when all confirmed members approve an item (like=TRUE or rating≥4), a decision_selection record should be created for that item.
**Validates: Requirements 6.2**

### Property 20: Threshold rule evaluation
*For any* decision with threshold rules, when the ratio of approvals to confirmed members meets or exceeds the threshold, a decision_selection record should be created.
**Validates: Requirements 6.3**

### Property 21: Selection snapshot preservation
*For any* decision_selection created, the snapshot field should contain vote tallies and rule parameters at the time of selection.
**Validates: Requirements 6.4**

### Property 22: Selection idempotency
*For any* item that meets approval rules, triggering the evaluation multiple times should result in only one decision_selection record.
**Validates: Requirements 6.6**

### Property 23: Tag filtering accuracy
*For any* tag filter applied to items, only items linked to the specified term via decision_item_term should be returned.
**Validates: Requirements 7.1**

### Property 24: Attribute filtering accuracy
*For any* JSONB attribute query, only items whose attributes match the query criteria should be returned.
**Validates: Requirements 7.2**

### Property 25: Combined filter intersection
*For any* combination of tag and attribute filters, only items matching all criteria should be returned.
**Validates: Requirements 7.3**

### Property 26: Pagination correctness
*For any* page size and page number, the returned items should be the correct subset of the total result set.
**Validates: Requirements 7.4**

### Property 27: Conversation idempotent creation
*For any* decision, opening it multiple times should result in exactly one conversation record.
**Validates: Requirements 8.1**

### Property 28: Message field persistence
*For any* message sent, all fields (sender, text, timestamp, read flag) should be stored and retrievable.
**Validates: Requirements 8.2**

### Property 29: Message chronological ordering
*For any* list of messages in a conversation, they should be ordered by sent_at timestamp in ascending order.
**Validates: Requirements 8.3**

### Property 30: Message read flag updates
*For any* message viewed by a user, the is_read flag should be updated to TRUE for that user's view.
**Validates: Requirements 8.4**

### Property 31: Chat access control
*For any* user attempting to access a decision's chat, access should be granted only if the user is a confirmed member of the owning group.
**Validates: Requirements 8.5**

### Property 32: Scoped question filtering
*For any* decision-scoped question query with a decision_id, only questions with matching scope and scope_key should be returned.
**Validates: Requirements 9.2**

### Property 33: Answer persistence
*For any* answer submission, the user_answer should be stored with correct question_id and optional decision_id references.
**Validates: Requirements 9.3**

### Property 34: Answer uniqueness enforcement
*For any* user, question, and decision combination, submitting multiple answers should update the existing answer rather than create duplicates.
**Validates: Requirements 9.4**

### Property 35: Decision closure prevents voting
*For any* closed decision, attempting to submit a new vote should be rejected.
**Validates: Requirements 10.2**

### Property 36: Closure preserves favourites
*For any* decision with existing favourites, closing the decision should not remove or modify any decision_selection records.
**Validates: Requirements 10.3**

### Property 37: Closed chat readability
*For any* closed decision, users should still be able to read existing messages in the conversation.
**Validates: Requirements 10.4**

### Property 38: Taxonomy name uniqueness
*For any* taxonomy, the key field should be unique across all taxonomies, preventing duplicate taxonomy names.
**Validates: Requirements 11.1**

### Property 39: Term taxonomy linking
*For any* term added to a taxonomy, the term should be linked to that taxonomy via taxonomy_id.
**Validates: Requirements 11.2**

### Property 40: Term metadata storage
*For any* term with UI metadata (color, icon), the attributes JSONB field should preserve all metadata.
**Validates: Requirements 11.3**

### Property 41: Taxonomy reusability
*For any* taxonomy and its terms, they should be usable across multiple decisions and item types without duplication.
**Validates: Requirements 11.4**

### Property 42: Decision access authorization
*For any* user attempting to access a decision, access should be granted only if the user is a confirmed member of the owning group or a shared group.
**Validates: Requirements 12.2**

### Property 43: Vote privacy preservation
*For any* vote summary query, individual voter identities should not be exposed, only aggregate counts.
**Validates: Requirements 12.3**

### Property 44: Role-based operation control
*For any* admin-only operation (e.g., closing decisions, removing members), the operation should succeed for admins and fail for regular members.
**Validates: Requirements 12.5**

### Property 45: Member removal threshold recalculation
*For any* threshold-based decision, when a confirmed member leaves the group, future threshold calculations should use the updated member count.
**Validates: Requirements 14.2**

### Property 46: Rule change non-retroactivity
*For any* decision with existing favourites, changing the approval rules should not remove existing decision_selection records.
**Validates: Requirements 14.3**

### Property 47: Decision sharing creates link
*For any* decision shared with another group, a decision_shared_group record should be created linking the decision to the target group.
**Validates: Requirements 15.1**

### Property 48: Shared decision threshold scope
*For any* shared decision with threshold rules, only confirmed members from the owning group should count toward the threshold calculation.
**Validates: Requirements 15.2**

### Property 49: Shared group access permissions
*For any* user in a shared group, they should be able to view and vote on the shared decision.
**Validates: Requirements 15.3**

## Error Handling

### Authentication Errors
- **Invalid Credentials**: Return 401 with generic message to prevent user enumeration
- **Expired Token**: Return 401 with token refresh instructions
- **Missing Token**: Return 401 with authentication required message

### Authorization Errors
- **Insufficient Permissions**: Return 403 when user lacks required role
- **Not Group Member**: Return 403 when accessing group-restricted resources
- **Decision Closed**: Return 400 when attempting to vote on closed decision

### Validation Errors
- **Missing Required Fields**: Return 400 with specific field errors
- **Invalid Data Types**: Return 400 with type mismatch details
- **Constraint Violations**: Return 409 for uniqueness violations
- **Invalid State Transitions**: Return 400 with valid transition options

### Resource Errors
- **Not Found**: Return 404 for non-existent resources
- **Already Exists**: Return 409 for duplicate creation attempts

### Database Errors
- **Connection Failures**: Return 503 with retry-after header
- **Trigger Failures**: Log error, return 500 with generic message
- **Transaction Conflicts**: Retry with exponential backoff, return 409 if persistent

## Testing Strategy

### Unit Testing

The system will use Django's built-in testing framework with pytest for unit tests. Unit tests will cover:

- **Model validation**: Test field constraints, default values, and custom validators
- **Serializer logic**: Test data transformation and validation rules
- **ViewSet permissions**: Test role-based access control for each endpoint
- **Business logic**: Test helper functions and utility methods
- **Edge cases**: Test boundary conditions like empty groups, zero thresholds, etc.

**Example unit test areas:**
- Password hashing and verification
- Token generation and validation
- Group membership status transitions
- Decision status state machine
- Vote constraint enforcement
- Message ordering and pagination

### Property-Based Testing

The system will use **Hypothesis** (Python property-based testing library) to verify universal properties across all valid inputs. Property-based tests will run a minimum of 100 iterations per property.

Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format:
```python
# Feature: generic-swipe-voting, Property N: [property text]
```

**Property test coverage:**
- **Authentication properties**: Password hashing, token validity, credential rejection (Properties 1-4)
- **Group management properties**: Auto-membership, invitations, status transitions (Properties 5-8)
- **Decision properties**: Field persistence, rule validation, status transitions (Properties 9-12)
- **Item properties**: Attribute storage, tagging, duplicate prevention (Properties 13-16)
- **Voting properties**: Vote storage, field requirements, rule evaluation (Properties 17-22)
- **Filtering properties**: Tag filtering, attribute queries, pagination (Properties 23-26)
- **Chat properties**: Conversation creation, message ordering, access control (Properties 27-31)
- **Questionnaire properties**: Scoped filtering, answer uniqueness (Properties 32-34)
- **Closure properties**: Vote prevention, favourite preservation (Properties 35-37)
- **Taxonomy properties**: Uniqueness, linking, reusability (Properties 38-41)
- **Authorization properties**: Access control, privacy, role-based operations (Properties 42-44)
- **Dynamic properties**: Threshold recalculation, rule changes, sharing (Properties 45-49)

**Hypothesis Strategies:**
- Generate random users with valid email formats and password complexity
- Generate random groups with varying member counts
- Generate random decisions with different rule configurations
- Generate random items with diverse JSONB attributes
- Generate random vote patterns to test approval thresholds
- Generate random tag combinations for filter testing

### Integration Testing

Integration tests will verify end-to-end workflows:

- **Complete voting flow**: Create group → invite members → create decision → add items → vote → verify favourites
- **Chat integration**: Create decision → send messages → verify ordering and read status
- **Filtering integration**: Create items with tags → apply filters → verify results
- **Authorization flow**: Test access control across group boundaries
- **Shared decision flow**: Share decision → verify cross-group access and voting

### Frontend Testing

- **Component tests**: Test React components in isolation using React Testing Library
- **Swipe gesture tests**: Test swipe event handlers and vote API calls
- **Integration tests**: Test complete user flows from UI to API
- **Responsive tests**: Verify mobile-first design across screen sizes

### Performance Testing

- **Load testing**: Simulate concurrent users voting on popular decisions
- **Query performance**: Verify GIN and BTREE indexes improve query times
- **Pagination efficiency**: Test large item sets with various page sizes
- **Trigger performance**: Measure trg_maybe_select_item execution time under load

## Mobile-First UI Design

### Swipe Interface

The core voting experience mimics Tinder's card-based interface:

**Card Stack Layout:**
```
┌─────────────────────────────┐
│                             │
│    ┌─────────────────┐      │
│    │                 │      │
│    │   Item Image    │      │
│    │                 │      │
│    ├─────────────────┤      │
│    │ Item Label      │      │
│    │ Key Attributes  │      │
│    │ Tags            │      │
│    └─────────────────┘      │
│                             │
│   ← Swipe Left  Right →     │
│                             │
└─────────────────────────────┘
```

**Swipe Gestures:**
- **Swipe Right**: Register positive vote (is_like=TRUE)
- **Swipe Left**: Register negative vote (is_like=FALSE)
- **Tap Card**: Show detailed view with all attributes
- **Swipe Up**: Add to personal shortlist (optional feature)

**Visual Feedback:**
- Card tilts in swipe direction
- Green overlay on right swipe
- Red overlay on left swipe
- Smooth animation as card exits
- Next card slides into view

### Responsive Breakpoints

- **Mobile**: < 768px (primary target)
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Touch Optimizations

- Minimum touch target size: 44x44px
- Swipe threshold: 100px horizontal movement
- Velocity detection for quick swipes
- Haptic feedback on vote registration (if supported)

## Security Considerations

### Authentication Security

- Passwords hashed with Argon2 (memory-hard algorithm)
- Token expiration: 24 hours for access tokens
- Refresh tokens: 30 days with rotation
- Rate limiting on login attempts: 5 attempts per 15 minutes

### Authorization Security

- All endpoints require authentication except signup/login
- Group membership verified on every decision/item access
- Role checks for admin operations (close decision, remove members)
- Shared group permissions validated for cross-group decisions

### Data Privacy

- Individual votes not exposed via API (only aggregates)
- Chat messages restricted to group members
- User profiles visible only to group co-members
- Email addresses not exposed in public APIs

### Input Validation

- All user inputs sanitized to prevent XSS
- SQL injection prevented by Django ORM parameterization
- JSONB attributes validated for structure and size limits
- File uploads (profile pictures) scanned and size-limited

### CORS Configuration

- Whitelist specific frontend origins
- Credentials allowed for authenticated requests
- Preflight caching for performance

## Deployment Architecture

### Backend Deployment

- **Application Server**: Gunicorn with multiple workers
- **Database**: PostgreSQL 14+ with connection pooling
- **Caching**: Redis for session storage and API caching
- **Static Files**: Served via CDN (CloudFront, Cloudflare)
- **Environment**: Docker containers orchestrated by Kubernetes or ECS

### Frontend Deployment

- **Build**: React production build with minification
- **Hosting**: Static hosting on S3 + CloudFront or Netlify
- **API Proxy**: CloudFront or Nginx for API routing
- **Environment Variables**: Injected at build time for API endpoints

### Database Migrations

- Django migrations for schema changes
- Trigger definitions managed in migration files
- Backward-compatible changes preferred
- Blue-green deployment for zero-downtime updates

## Scalability Considerations

### Database Optimization

- **Indexes**: GIN on JSONB, BTREE on foreign keys and timestamps
- **Partitioning**: Consider partitioning decision_vote by decision_id for very large datasets
- **Read Replicas**: Route read-heavy queries to replicas
- **Connection Pooling**: PgBouncer for efficient connection management

### Caching Strategy

- **API Response Caching**: Cache GET requests for decisions, items, taxonomies
- **Cache Invalidation**: Invalidate on POST/PATCH/DELETE operations
- **Session Caching**: Store user sessions in Redis
- **Query Result Caching**: Cache expensive aggregate queries

### Horizontal Scaling

- **Stateless Backend**: All application servers identical, no local state
- **Load Balancer**: Distribute requests across multiple backend instances
- **Database Scaling**: Vertical scaling first, then read replicas
- **CDN**: Offload static assets and API responses where possible

## Future Enhancements

### Phase 2 Features

- **Real-time Updates**: WebSocket support for live favourite notifications
- **Push Notifications**: Mobile push for new items, favourites, chat messages
- **Advanced Rules**: Min count rules (e.g., "≥2 likes"), weighted voting
- **Item Recommendations**: ML-based suggestions based on user preferences
- **Export/Import**: CSV/JSON export of decisions and results
- **Analytics Dashboard**: Visualize voting patterns and engagement metrics

### Phase 3 Features

- **Multi-language Support**: i18n for global audiences
- **Accessibility**: WCAG 2.1 AA compliance, screen reader support
- **Offline Mode**: PWA with offline voting queue
- **Video/Audio Items**: Support for multimedia item types
- **Collaborative Filtering**: Show "users like you also liked..."
- **Integration APIs**: Webhooks for external system integration

