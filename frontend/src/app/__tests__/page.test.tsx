import { render, screen } from '@testing-library/react';
import { AuthProvider } from '@/contexts/AuthContext';
import HomePage from '../page';

// Mock the components that have external dependencies
jest.mock('@/components/Header', () => {
  return function MockHeader() {
    return <div data-testid="header">Header</div>;
  };
});

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock the auth context
const mockAuthContextValue = {
  user: null,
  isLoading: false,
  login: jest.fn(),
  signup: jest.fn(),
  logout: jest.fn(),
};

const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <div data-testid="auth-provider">
      {children}
    </div>
  );
};

jest.mock('@/contexts/AuthContext', () => ({
  AuthProvider: MockAuthProvider,
  useAuth: () => mockAuthContextValue,
}));

describe('Home Page', () => {
  it('renders the landing page', () => {
    render(<HomePage />);
    
    // Check for main heading
    expect(screen.getByText(/Professional Image Processing/i)).toBeInTheDocument();
    
    // Check for key features
    expect(screen.getByText(/AI-Powered Processing/i)).toBeInTheDocument();
    expect(screen.getByText(/Async Processing/i)).toBeInTheDocument();
    expect(screen.getByText(/Secure & Reliable/i)).toBeInTheDocument();
  });

  it('renders the pricing section', () => {
    render(<HomePage />);
    
    // Check for pricing plans
    expect(screen.getByText(/Choose Your Plan/i)).toBeInTheDocument();
    expect(screen.getByText(/Starter/i)).toBeInTheDocument();
    expect(screen.getByText(/Professional/i)).toBeInTheDocument();
    expect(screen.getByText(/Enterprise/i)).toBeInTheDocument();
  });

  it('renders call-to-action buttons', () => {
    render(<HomePage />);
    
    // Check for CTA buttons
    const getStartedButtons = screen.getAllByText(/Get Started/i);
    expect(getStartedButtons.length).toBeGreaterThan(0);
  });
});
