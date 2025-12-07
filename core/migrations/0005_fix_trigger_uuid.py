# Generated manually to fix trigger UUID generation

from django.db import migrations


def fix_trigger(apps, schema_editor):
    """Fix the approval rule evaluation trigger to generate UUIDs"""
    schema_editor.execute("""
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
                    INSERT INTO decision_selection (id, decision_id, item_id, selected_at, snapshot)
                    VALUES (
                        gen_random_uuid(),
                        v_decision_id,
                        NEW.item_id,
                        NOW(),
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
                        INSERT INTO decision_selection (id, decision_id, item_id, selected_at, snapshot)
                        VALUES (
                            gen_random_uuid(),
                            v_decision_id,
                            NEW.item_id,
                            NOW(),
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
    """)


def revert_trigger(apps, schema_editor):
    """Revert to the old trigger (without UUID generation)"""
    schema_editor.execute("""
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
    """)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_vote_constraint'),
    ]

    operations = [
        migrations.RunPython(fix_trigger, revert_trigger),
    ]
