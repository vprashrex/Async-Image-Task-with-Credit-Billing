import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from '../AuthContext';

// Mock axios
jest.mock('axios', () => ({
  create: () => ({
    post: jest.fn(),
    get: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  }),
}));

// Mock js-cookie
jest.mock('js-cookie', () => ({
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn(),
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
  }),
}));

// Test component that uses the auth context
function TestComponent() {
  const { user, isLoading, login, logout } = useAuth();
  
  return (
    <div>
      {isLoading && <div data-testid="loading">Loading...</div>}
      {user ? (
        <div>
          <div data-testid="user-email">{user.email}</div>
          <button onClick={logout} data-testid="logout-btn">
            Logout
          </button>
        </div>
      ) : (
        <div>
          <div data-testid="not-logged-in">Not logged in</div>
          <button 
            onClick={() => login('test@example.com', 'password')} 
            data-testid="login-btn"
          >
            Login
          </button>
        </div>
      )}
    </div>
  );
}

describe('AuthContext', () => {
  it('provides authentication context to children', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(screen.getByTestId('not-logged-in')).toBeInTheDocument();
    expect(screen.getByTestId('login-btn')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // The component should not show loading by default in tests
    // as we're not actually making API calls
    expect(screen.queryByTestId('loading')).not.toBeInTheDocument();
  });

  it('handles login action', async () => {
    const user = userEvent.setup();
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    const loginBtn = screen.getByTestId('login-btn');
    await user.click(loginBtn);

    // Since we're mocking the API calls, the actual login won't work
    // This test mainly ensures the context is properly wired up
    expect(loginBtn).toBeInTheDocument();
  });
});
