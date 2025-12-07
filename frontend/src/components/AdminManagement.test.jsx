import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import JoinRequestsList from './JoinRequestsList';
import RejectedInvitationsList from './RejectedInvitationsList';
import RejectedRequestsList from './RejectedRequestsList';

/**
 * Feature: group-invitation-requests, Property 15: Action button visibility
 * Validates: Requirements 4.1, 8.2, 9.2
 * 
 * Property: For any rejected membership, the appropriate action buttons 
 * (Resend/Delete) should be displayed based on membership_type and user role.
 */
describe('Admin Management Components - Action Button Visibility', () => {
  const mockOnApprove = vi.fn();
  const mockOnReject = vi.fn();
  const mockOnResend = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnSuccess = vi.fn();
  const mockOnError = vi.fn();

  /**
   * Property: Pending join requests should display Approve and Reject buttons
   * Validates: Requirement 7.2
   */
  it('should display Approve and Reject buttons for pending join requests', () => {
    const requests = [
      {
        id: 'req-1',
        user: { username: 'testuser' },
        invited_at: new Date().toISOString(),
        status: 'pending',
      },
    ];

    render(
      <JoinRequestsList
        requests={requests}
        onApprove={mockOnApprove}
        onReject={mockOnReject}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display both Approve and Reject buttons
    expect(screen.getByText('Approve')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
    
    // Should not display Resend or Delete buttons
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();
  });

  /**
   * Property: Rejected invitations should display Resend and Delete buttons
   * Validates: Requirement 8.2
   */
  it('should display Resend and Delete buttons for rejected invitations', () => {
    const invitations = [
      {
        id: 'inv-1',
        user: { username: 'testuser' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
    ];

    render(
      <RejectedInvitationsList
        invitations={invitations}
        onResend={mockOnResend}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display both Resend and Delete buttons
    expect(screen.getByText('Resend')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
    
    // Should not display Approve or Reject buttons
    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
  });

  /**
   * Property: Rejected requests should display only Delete button (no Resend)
   * Validates: Requirement 9.2
   */
  it('should display only Delete button for rejected requests', () => {
    const requests = [
      {
        id: 'req-1',
        user: { username: 'testuser' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
    ];

    render(
      <RejectedRequestsList
        requests={requests}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display only Delete button
    expect(screen.getByText('Delete')).toBeInTheDocument();
    
    // Should not display Resend, Approve, or Reject buttons
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
  });

  /**
   * Property: Multiple pending requests should all display action buttons
   */
  it('should display action buttons for all pending requests', () => {
    const requests = [
      {
        id: 'req-1',
        user: { username: 'user1' },
        invited_at: new Date().toISOString(),
        status: 'pending',
      },
      {
        id: 'req-2',
        user: { username: 'user2' },
        invited_at: new Date().toISOString(),
        status: 'pending',
      },
      {
        id: 'req-3',
        user: { username: 'user3' },
        invited_at: new Date().toISOString(),
        status: 'pending',
      },
    ];

    render(
      <JoinRequestsList
        requests={requests}
        onApprove={mockOnApprove}
        onReject={mockOnReject}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display Approve and Reject buttons for each request
    const approveButtons = screen.getAllByText('Approve');
    const rejectButtons = screen.getAllByText('Reject');
    
    expect(approveButtons).toHaveLength(3);
    expect(rejectButtons).toHaveLength(3);
  });

  /**
   * Property: Multiple rejected invitations should all display action buttons
   */
  it('should display action buttons for all rejected invitations', () => {
    const invitations = [
      {
        id: 'inv-1',
        user: { username: 'user1' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
      {
        id: 'inv-2',
        user: { username: 'user2' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
    ];

    render(
      <RejectedInvitationsList
        invitations={invitations}
        onResend={mockOnResend}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display Resend and Delete buttons for each invitation
    const resendButtons = screen.getAllByText('Resend');
    const deleteButtons = screen.getAllByText('Delete');
    
    expect(resendButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });

  /**
   * Property: Multiple rejected requests should all display Delete button
   */
  it('should display Delete button for all rejected requests', () => {
    const requests = [
      {
        id: 'req-1',
        user: { username: 'user1' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
      {
        id: 'req-2',
        user: { username: 'user2' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
      {
        id: 'req-3',
        user: { username: 'user3' },
        invited_at: new Date().toISOString(),
        rejected_at: new Date().toISOString(),
        status: 'rejected',
      },
    ];

    render(
      <RejectedRequestsList
        requests={requests}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should display Delete button for each request
    const deleteButtons = screen.getAllByText('Delete');
    expect(deleteButtons).toHaveLength(3);
    
    // Should not display any Resend buttons
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
  });

  /**
   * Property: Empty lists should not display any action buttons
   */
  it('should not display action buttons when lists are empty', () => {
    const { rerender } = render(
      <JoinRequestsList
        requests={[]}
        onApprove={mockOnApprove}
        onReject={mockOnReject}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    // Should not display any action buttons
    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();

    // Test RejectedInvitationsList
    rerender(
      <RejectedInvitationsList
        invitations={[]}
        onResend={mockOnResend}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();

    // Test RejectedRequestsList
    rerender(
      <RejectedRequestsList
        requests={[]}
        onDelete={mockOnDelete}
        onSuccess={mockOnSuccess}
        onError={mockOnError}
      />
    );

    expect(screen.queryByText('Approve')).not.toBeInTheDocument();
    expect(screen.queryByText('Reject')).not.toBeInTheDocument();
    expect(screen.queryByText('Resend')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();
  });
});
