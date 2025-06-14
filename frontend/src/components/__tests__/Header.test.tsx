import { render, screen } from '@testing-library/react';
import { Header } from '../Header';
import { useAuth } from '@/contexts/AuthContext';

// Mock the auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('Header Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly when user is not logged in', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: false,
      login: jest.fn(),
      signup: jest.fn(),
      logout: jest.fn(),
    });

    render(<Header />);

    expect(screen.getByText('Virtual Space Tech')).toBeInTheDocument();
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Sign Up')).toBeInTheDocument();
  });

  it('renders correctly when user is logged in', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      username: 'testuser',
      credits: 10,
      is_admin: false,
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      login: jest.fn(),
      signup: jest.fn(),
      logout: jest.fn(),
    });

    render(<Header />);

    expect(screen.getByText('Virtual Space Tech')).toBeInTheDocument();
    expect(screen.getByText('testuser')).toBeInTheDocument();
    expect(screen.getByText('10 Credits')).toBeInTheDocument();
  });

  it('shows admin link for admin users', () => {
    const mockUser = {
      id: '1',
      email: 'admin@example.com',
      username: 'admin',
      credits: 100,
      is_admin: true,
    };

    mockUseAuth.mockReturnValue({
      user: mockUser,
      isLoading: false,
      login: jest.fn(),
      signup: jest.fn(),
      logout: jest.fn(),
    });

    render(<Header />);

    expect(screen.getByText('Admin')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      isLoading: true,
      login: jest.fn(),
      signup: jest.fn(),
      logout: jest.fn(),
    });

    render(<Header />);

    expect(screen.getByText('Virtual Space Tech')).toBeInTheDocument();
    // When loading, buttons shouldn't be rendered yet
    expect(screen.queryByText('Login')).not.toBeInTheDocument();
  });
});
