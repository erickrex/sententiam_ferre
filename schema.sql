-- Sententiam Ferre Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Account Table
CREATE TABLE user_account (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_account_username ON user_account(username);
CREATE INDEX idx_user_account_email ON user_account(email);

-- App Group Table
CREATE TABLE app_group (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_app_group_created_by ON app_group(created_by);

-- Group Membership Table
CREATE TABLE group_membership (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES app_group(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(group_id, user_id)
);

CREATE INDEX idx_group_membership_group_confirmed ON group_membership(group_id, is_confirmed);
CREATE INDEX idx_group_membership_user ON group_membership(user_id);

-- Decision Table
CREATE TABLE decision (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID NOT NULL REFERENCES app_group(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    item_type VARCHAR(100),
    rules JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('draft', 'open', 'closed', 'archived'))
);

CREATE INDEX idx_decision_group ON decision(group_id);
CREATE INDEX idx_decision_status ON decision(status);

-- Decision Shared Group Table (for cross-group decisions)
CREATE TABLE decision_shared_group (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL REFERENCES decision(id) ON DELETE CASCADE,
    group_id UUID NOT NULL REFERENCES app_group(id) ON DELETE CASCADE,
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_id, group_id)
);

CREATE INDEX idx_decision_shared_group_decision ON decision_shared_group(decision_id);
CREATE INDEX idx_decision_shared_group_group ON decision_shared_group(group_id);

-- Catalog Item Table (reusable item templates)
CREATE TABLE catalog_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    label VARCHAR(255) NOT NULL,
    attributes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_catalog_item_attributes ON catalog_item USING GIN(attributes);

-- Decision Item Table
CREATE TABLE decision_item (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL REFERENCES decision(id) ON DELETE CASCADE,
    catalog_item_id UUID REFERENCES catalog_item(id) ON DELETE SET NULL,
    label VARCHAR(255) NOT NULL,
    attributes JSONB,
    external_ref VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(decision_id, external_ref, label)
);

CREATE INDEX idx_decision_item_decision ON decision_item(decision_id);
CREATE INDEX idx_decision_item_attributes ON decision_item USING GIN(attributes);
CREATE INDEX idx_decision_item_catalog ON decision_item(catalog_item_id);

-- Decision Vote Table
CREATE TABLE decision_vote (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES decision_item(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    is_like BOOLEAN,
    rating INTEGER,
    weight DECIMAL(5, 2) DEFAULT 1.0,
    note TEXT,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, item_id),
    CHECK (is_like IS NOT NULL OR rating IS NOT NULL)
);

CREATE INDEX idx_decision_vote_item ON decision_vote(item_id);
CREATE INDEX idx_decision_vote_user ON decision_vote(user_id);

-- Decision Selection Table (Favourites)
CREATE TABLE decision_selection (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL REFERENCES decision(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES decision_item(id) ON DELETE CASCADE,
    selected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    snapshot JSONB,
    UNIQUE(decision_id, item_id)
);

CREATE INDEX idx_decision_selection_decision ON decision_selection(decision_id);
CREATE INDEX idx_decision_selection_item ON decision_selection(item_id);

-- Conversation Table
CREATE TABLE conversation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID NOT NULL UNIQUE REFERENCES decision(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conversation_decision ON conversation(decision_id);

-- Message Table
CREATE TABLE message (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_message_conversation_sent ON message(conversation_id, sent_at);
CREATE INDEX idx_message_sender ON message(sender_id);

-- Taxonomy Table
CREATE TABLE taxonomy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE INDEX idx_taxonomy_name ON taxonomy(name);

-- Term Table
CREATE TABLE term (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    taxonomy_id UUID NOT NULL REFERENCES taxonomy(id) ON DELETE CASCADE,
    value VARCHAR(255) NOT NULL,
    attributes JSONB,
    UNIQUE(taxonomy_id, value)
);

CREATE INDEX idx_term_taxonomy ON term(taxonomy_id);

-- Decision Item Term Table (tagging)
CREATE TABLE decision_item_term (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES decision_item(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES term(id) ON DELETE CASCADE,
    UNIQUE(item_id, term_id)
);

CREATE INDEX idx_decision_item_term_item ON decision_item_term(item_id);
CREATE INDEX idx_decision_item_term_term ON decision_item_term(term_id);

-- Catalog Item Term Table (tagging for catalog items)
CREATE TABLE catalog_item_term (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_item_id UUID NOT NULL REFERENCES catalog_item(id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES term(id) ON DELETE CASCADE,
    UNIQUE(catalog_item_id, term_id)
);

CREATE INDEX idx_catalog_item_term_catalog ON catalog_item_term(catalog_item_id);
CREATE INDEX idx_catalog_item_term_term ON catalog_item_term(term_id);

-- Question Table
CREATE TABLE question (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    text TEXT NOT NULL,
    scope VARCHAR(50) NOT NULL,
    item_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (scope IN ('global', 'item_type', 'decision', 'group'))
);

CREATE INDEX idx_question_scope ON question(scope);

-- Answer Option Table
CREATE TABLE answer_option (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    text VARCHAR(255) NOT NULL,
    order_num INTEGER NOT NULL
);

CREATE INDEX idx_answer_option_question ON answer_option(question_id);

-- User Answer Table
CREATE TABLE user_answer (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES question(id) ON DELETE CASCADE,
    decision_id UUID REFERENCES decision(id) ON DELETE CASCADE,
    answer_option_id UUID REFERENCES answer_option(id) ON DELETE SET NULL,
    answer_value JSONB,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, question_id, decision_id)
);

CREATE INDEX idx_user_answer_user ON user_answer(user_id);
CREATE INDEX idx_user_answer_question ON user_answer(question_id);
CREATE INDEX idx_user_answer_decision ON user_answer(decision_id);

-- Trigger Function: Evaluate approval rules and create favourites
CREATE OR REPLACE FUNCTION fn_maybe_select_item()
RETURNS TRIGGER AS $$
DECLARE
    v_decision_id UUID;
    v_rules JSONB;
    v_rule_type TEXT;
    v_threshold DECIMAL;
    v_confirmed_members INTEGER;
    v_approvals INTEGER;
    v_total_votes INTEGER;
    v_approval_ratio DECIMAL;
BEGIN
    -- Get decision_id and rules
    SELECT di.decision_id, d.rules
    INTO v_decision_id, v_rules
    FROM decision_item di
    JOIN decision d ON d.id = di.decision_id
    WHERE di.id = NEW.item_id;

    -- Extract rule type
    v_rule_type := v_rules->>'type';

    -- Count confirmed members in the owning group
    SELECT COUNT(*)
    INTO v_confirmed_members
    FROM group_membership gm
    JOIN decision d ON d.group_id = gm.group_id
    WHERE d.id = v_decision_id
    AND gm.is_confirmed = TRUE;

    -- Count approvals (is_like = TRUE or rating >= 4)
    SELECT COUNT(*)
    INTO v_approvals
    FROM decision_vote
    WHERE item_id = NEW.item_id
    AND (is_like = TRUE OR rating >= 4);

    -- Count total votes
    SELECT COUNT(*)
    INTO v_total_votes
    FROM decision_vote
    WHERE item_id = NEW.item_id;

    -- Evaluate rules
    IF v_rule_type = 'unanimous' THEN
        -- Unanimous: all confirmed members must approve
        IF v_approvals = v_confirmed_members AND v_confirmed_members > 0 THEN
            INSERT INTO decision_selection (decision_id, item_id, snapshot)
            VALUES (
                v_decision_id,
                NEW.item_id,
                jsonb_build_object(
                    'approvals', v_approvals,
                    'total_members', v_confirmed_members,
                    'rule', v_rules
                )
            )
            ON CONFLICT (decision_id, item_id) DO NOTHING;
        END IF;
    ELSIF v_rule_type = 'threshold' THEN
        -- Threshold: approval ratio must meet or exceed threshold
        v_threshold := (v_rules->>'value')::DECIMAL;
        IF v_confirmed_members > 0 THEN
            v_approval_ratio := v_approvals::DECIMAL / v_confirmed_members::DECIMAL;
            IF v_approval_ratio >= v_threshold THEN
                INSERT INTO decision_selection (decision_id, item_id, snapshot)
                VALUES (
                    v_decision_id,
                    NEW.item_id,
                    jsonb_build_object(
                        'approvals', v_approvals,
                        'total_members', v_confirmed_members,
                        'threshold', v_threshold,
                        'approval_ratio', v_approval_ratio,
                        'rule', v_rules
                    )
                )
                ON CONFLICT (decision_id, item_id) DO NOTHING;
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Evaluate approval rules on vote insert/update
CREATE TRIGGER trg_maybe_select_item
AFTER INSERT OR UPDATE ON decision_vote
FOR EACH ROW
EXECUTE FUNCTION fn_maybe_select_item();
