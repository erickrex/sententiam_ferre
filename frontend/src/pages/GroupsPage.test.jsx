import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GroupsPage from './GroupsPage';
import { groupsAPI } from '../services/api';

// Mock the API
vi.mock('../services/api', () => ({
  groupsAPI: {
    list: vi.fn(),
  },
}));

// Mock child components to simplify testing
vi.mock('../components/MyGroupsTab', () => ({
  default: () => <div data-testid="my-groups-tab">My Groups Tab</div>,
}));

vi.mock('../components/JoinTab', () => ({
  default: () => <div data-testid="join-tab">Join Tab</div>,
}));

vi.mock('../components/CreateGroupForm', () => ({
  default: () => <div data-testid="create-group-form">Create Group Form</div>,
}));

describe('GroupsPage Tab Display', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    groupsAPI.list.mockResolvedValue({
      data: { data: [] },
    });
  });

  /**
   * Feature: group-invitation-requests, Property 14: Tab display order
   * Validates: Requirements 1.2, 1.3
   * 
   * Property: For any groups page load, tabs should be displayed in order:
   * "My Groups" (default), "Join", "Create"
   */
  it('should display My Groups tab first (default), Join second, and Create third', async () => {
    render(
      <BrowserRouter>
        <GroupsPage />
      </BrowserRouter>
    );

    // Wait for component to render
    await waitFor(() => {
      expect(screen.getByText('Groups')).toBeInTheDocument();
    });

    // Get all tab buttons
    const tabButtons = screen.getAllByRole('tab');

    // Verify we have exactly 3 tabs
    expect(tabButtons).toHaveLength(3);

    // Verify first tab is "My Groups"
    expect(tabButtons[0]).toHaveTextContent('My Groups');

    // Verify second tab is "Join"
    expect(tabButtons[1]).toHaveTextContent('Join');

    // Verify third tab is "Create"
    expect(tabButtons[2]).toHaveTextContent('Create');

    // Verify My Groups tab is active by default (first tab, index 0)
    expect(tabButtons[0]).toHaveClass('active');
    expect(tabButtons[1]).not.toHaveClass('active');
    expect(tabButtons[2]).not.toHaveClass('active');

    // Verify My Groups tab content is displayed
    expect(screen.getByTestId('my-groups-tab')).toBeInTheDocument();
  });

  /**
   * Property test: Tab order should be consistent across multiple renders
   */
  it('should maintain tab order across multiple renders', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <GroupsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Groups')).toBeInTheDocument();
    });

    // Check initial order
    let tabButtons = screen.getAllByRole('tab');
    expect(tabButtons[0]).toHaveTextContent('My Groups');
    expect(tabButtons[1]).toHaveTextContent('Join');
    expect(tabButtons[2]).toHaveTextContent('Create');

    // Unmount and remount
    unmount();
    
    render(
      <BrowserRouter>
        <GroupsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Groups')).toBeInTheDocument();
    });

    // Check order after remount
    tabButtons = screen.getAllByRole('tab');
    expect(tabButtons[0]).toHaveTextContent('My Groups');
    expect(tabButtons[1]).toHaveTextContent('Join');
    expect(tabButtons[2]).toHaveTextContent('Create');
  });

  /**
   * Property test: Default tab should always be My Groups (index 0)
   */
  it('should always default to My Groups tab on initial load', async () => {
    // Test multiple times to ensure consistency
    for (let i = 0; i < 5; i++) {
      const { unmount } = render(
        <BrowserRouter>
          <GroupsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Groups')).toBeInTheDocument();
      });

      const tabButtons = screen.getAllByRole('tab');
      
      // My Groups tab (first tab) should be active
      expect(tabButtons[0]).toHaveClass('active');
      expect(tabButtons[0]).toHaveTextContent('My Groups');
      
      // Other tabs should not be active
      expect(tabButtons[1]).not.toHaveClass('active');
      expect(tabButtons[2]).not.toHaveClass('active');

      unmount();
    }
  });
});
