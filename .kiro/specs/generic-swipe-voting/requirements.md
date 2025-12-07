# Requirements Document

## Introduction

Sententiam Ferre is a collaborative decision-making application that enables groups of users to reach consensus on items through swipe-style voting. The system supports N-person participation where users vote on items, and those meeting configured approval rules automatically move to a shared Favourites list. Each decision includes integrated chat functionality for group discussion. The application uses a mobile-first design approach with Django Rest Framework backend and React JavaScript frontend.

## Glossary

- **User**: An authenticated person who can create or participate in groups and decisions
- **Group**: A collection of users collaborating on decisions (stored as app_group)
- **Organizer**: A user who creates and manages groups and decisions
- **Participant**: A user who votes on items and engages in decision discussions
- **Decision**: A single voting topic within a group with configured approval rules
- **Item**: A candidate option within a decision that users can vote on (stored as decision_item)
- **Vote**: A user's reaction to an item, expressed as like/dislike or rating
- **Favourite**: An item that has met the decision's approval rule (stored as decision_selection)
- **Taxonomy**: A classification system for organizing items (e.g., category, origin)
- **Term**: A specific value within a taxonomy used to tag items
- **Questionnaire**: A set of questions to capture user preferences
- **Conversation**: A chat thread associated with a decision
- **Approval Rule**: A JSON configuration defining when items become favourites (unanimous or threshold-based)
- **Confirmed Member**: A user who has accepted a group invitation
- **Swipe**: A mobile-first interaction pattern for voting on items

## Requirements

### Requirement 1

**User Story:** As a new user, I want to create an account and authenticate, so that I can participate in group decisions.

#### Acceptance Criteria

1. WHEN a user submits valid registration information THEN the System SHALL create a user_account with hashed password using Argon2 or BCrypt
2. WHEN a user submits valid login credentials THEN the System SHALL authenticate the user and return a session token
3. WHEN a user submits invalid credentials THEN the System SHALL reject authentication and maintain system security
4. THE System SHALL enforce password complexity requirements during registration

### Requirement 2

**User Story:** As an organizer, I want to create a group and invite other users, so that we can collaborate on decisions together.

#### Acceptance Criteria

1. WHEN an organizer creates a group THEN the System SHALL create an app_group record and add the organizer as a confirmed group_membership
2. WHEN an organizer invites a registered user to a group THEN the System SHALL create a group_membership record with is_confirmed set to FALSE
3. WHEN an organizer attempts to invite a non-registered user THEN the System SHALL prompt for user registration before allowing invitation
4. WHEN an invited user accepts an invitation THEN the System SHALL set the group_membership is_confirmed field to TRUE
5. WHEN an invited user declines an invitation THEN the System SHALL delete the group_membership record

### Requirement 3

**User Story:** As an organizer, I want to create a decision with specific approval rules, so that the group can vote on items according to our preferences.

#### Acceptance Criteria

1. WHEN an organizer creates a decision THEN the System SHALL store the title, description, item_type, rules JSON, and status fields
2. WHEN an organizer specifies unanimous approval rules THEN the System SHALL store rules as JSON with type "unanimous"
3. WHEN an organizer specifies threshold approval rules THEN the System SHALL store rules as JSON with type "threshold" and a numeric value between 0 and 1
4. WHEN a decision is created THEN the System SHALL set the initial status to "open"
5. WHEN an organizer updates decision status THEN the System SHALL transition through valid states: draft, open, closed, or archived

### Requirement 4

**User Story:** As an organizer, I want to add items to a decision with attributes and tags, so that participants have options to vote on.

#### Acceptance Criteria

1. WHEN an organizer adds an item to a decision THEN the System SHALL store the item with a label and attributes in JSONB format
2. WHEN an organizer links an item to a catalog entry THEN the System SHALL store the catalog_item_id reference
3. WHEN an organizer tags an item with a term THEN the System SHALL create a decision_item_term record linking the item to the taxonomy term
4. WHEN an organizer adds multiple items THEN the System SHALL prevent duplicate items using external_ref and label uniqueness per decision
5. THE System SHALL index decision_item attributes using GIN for efficient querying

### Requirement 5

**User Story:** As a participant, I want to swipe and vote on items, so that I can express my preferences to the group.

#### Acceptance Criteria

1. WHEN a participant votes on an item THEN the System SHALL create or update a decision_vote record with is_like or rating values
2. WHEN a participant submits a vote THEN the System SHALL enforce that each user can vote only once per item using UNIQUE constraint on user_id and item_id
3. WHEN a participant updates their vote THEN the System SHALL modify the existing decision_vote record
4. WHEN a vote is submitted THEN the System SHALL ensure at least one of is_like or rating is provided
5. THE System SHALL support mobile swipe gestures for like and dislike actions

### Requirement 6

**User Story:** As a participant, I want items that meet approval rules to automatically appear in Favourites, so that the group can see which options have consensus.

#### Acceptance Criteria

1. WHEN votes are cast on an item THEN the System SHALL evaluate the decision's approval rules via trigger trg_maybe_select_item
2. WHEN unanimous rules are configured and all confirmed members approve an item THEN the System SHALL insert a decision_selection record for that item
3. WHEN threshold rules are configured and approvals divided by confirmed members meets or exceeds the threshold value THEN the System SHALL insert a decision_selection record for that item
4. WHEN a decision_selection is created THEN the System SHALL store a snapshot of vote tallies and parameters at selection time
5. WHEN an item becomes a favourite THEN the System SHALL display it in the Favourites list within one second
6. THE System SHALL use ON CONFLICT DO NOTHING to ensure trigger idempotency

### Requirement 7

**User Story:** As a participant, I want to filter and search items by tags and attributes, so that I can find relevant options quickly.

#### Acceptance Criteria

1. WHEN a participant applies tag filters THEN the System SHALL return only items linked to the specified terms via decision_item_term
2. WHEN a participant queries JSON attributes THEN the System SHALL use GIN indexes to efficiently filter items by attribute values
3. WHEN a participant combines multiple filters THEN the System SHALL return items matching all specified criteria
4. THE System SHALL support pagination for item lists to handle large datasets

### Requirement 8

**User Story:** As a participant, I want to chat with other group members about the decision, so that we can discuss options and reach consensus.

#### Acceptance Criteria

1. WHEN a participant opens a decision THEN the System SHALL create a conversation record if one does not exist
2. WHEN a participant sends a message THEN the System SHALL store the message with sender, text, timestamp, and read flag
3. WHEN messages are displayed THEN the System SHALL sort them by sent_at timestamp in ascending order
4. WHEN a participant views messages THEN the System SHALL update read flags for that user
5. THE System SHALL restrict chat access to confirmed group members only

### Requirement 9

**User Story:** As a participant, I want to answer preference questionnaires, so that the system can better understand my preferences.

#### Acceptance Criteria

1. WHEN a questionnaire is configured with global scope THEN the System SHALL display questions to all users
2. WHEN a questionnaire is configured with decision scope THEN the System SHALL display questions only within that decision context
3. WHEN a participant submits an answer THEN the System SHALL store the user_answer with question_id and optional decision_id
4. WHEN a participant answers a question THEN the System SHALL enforce UNIQUE constraint on user_id, question_id, and decision_id to prevent duplicate answers
5. THE System SHALL support both free-form answers via answer_value JSON and predefined answer_option selections

### Requirement 10

**User Story:** As an organizer, I want to close a decision, so that voting stops while preserving the results and discussion history.

#### Acceptance Criteria

1. WHEN an organizer closes a decision THEN the System SHALL update the status to "closed"
2. WHEN a decision is closed THEN the System SHALL prevent new votes from being submitted
3. WHEN a decision is closed THEN the System SHALL maintain all existing favourites in decision_selection
4. WHEN a decision is closed THEN the System SHALL keep the conversation readable but may restrict new messages
5. WHEN an organizer archives a decision THEN the System SHALL update the status to "archived"

### Requirement 11

**User Story:** As an administrator, I want to manage taxonomies and terms, so that items can be consistently categorized across decisions.

#### Acceptance Criteria

1. WHEN an administrator creates a taxonomy THEN the System SHALL store the taxonomy with a unique name
2. WHEN an administrator adds terms to a taxonomy THEN the System SHALL create term records linked to that taxonomy
3. WHEN terms are created THEN the System SHALL support storing UI metadata in attributes JSONB field for color and icon information
4. THE System SHALL allow reuse of taxonomies and terms across multiple decisions and item types

### Requirement 12

**User Story:** As a system, I want to enforce security and privacy controls, so that user data and group decisions remain protected.

#### Acceptance Criteria

1. THE System SHALL hash all passwords using Argon2 or BCrypt before storage
2. WHEN a user attempts to access a decision THEN the System SHALL verify the user is a confirmed member of the owning group
3. WHEN a user attempts to view votes THEN the System SHALL display only aggregate vote counts, not individual user votes
4. WHEN a user attempts to access chat messages THEN the System SHALL verify the user is a confirmed group member
5. THE System SHALL enforce role-based access control distinguishing group admins from regular members

### Requirement 13

**User Story:** As a user, I want a mobile-first interface with swipe interactions, so that I can use the app naturally on my smartphone.

#### Acceptance Criteria

1. THE System SHALL implement a React JavaScript frontend optimized for mobile screen sizes
2. WHEN a user views items on mobile THEN the System SHALL display them in a card-based swipe interface similar to Tinder
3. WHEN a user swipes right on an item THEN the System SHALL register a positive vote
4. WHEN a user swipes left on an item THEN the System SHALL register a negative vote
5. THE System SHALL provide responsive design that adapts to desktop browsers while prioritizing mobile experience

### Requirement 14

**User Story:** As a system, I want to maintain data integrity and reliability, so that voting results are accurate and consistent.

#### Acceptance Criteria

1. THE System SHALL use database triggers to automatically evaluate approval rules after vote changes
2. WHEN a group member leaves THEN the System SHALL recalculate threshold-based favourites using remaining confirmed members
3. WHEN approval rules are modified mid-decision THEN the System SHALL apply new rules to future selections without removing existing favourites
4. THE System SHALL maintain audit trails in decision_selection snapshot field showing vote tallies at selection time
5. THE System SHALL use database indexes on conversation_id and sent_at for efficient message retrieval

### Requirement 15

**User Story:** As an organizer, I want to share decisions across multiple groups, so that larger communities can collaborate on the same items.

#### Acceptance Criteria

1. WHEN an organizer shares a decision with another group THEN the System SHALL create a decision_shared_group record
2. WHEN calculating approval thresholds for shared decisions THEN the System SHALL count confirmed members from the owning group
3. WHEN a user from a shared group accesses the decision THEN the System SHALL grant appropriate viewing and voting permissions
