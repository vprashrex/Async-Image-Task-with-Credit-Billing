# Virtual Space Tech - Async Image Task SaaS Frontend

A modern, responsive frontend for an Async Image Task SaaS platform built with Next.js, TypeScript, and TailwindCSS. This application allows users to upload images for AI-powered processing, manage tasks, purchase credits, and includes a comprehensive admin panel.

## 🚀 Features

### User Features
- **Authentication**: Secure JWT-based login and registration
- **Image Upload**: Drag-and-drop image upload with validation and preview
- **Task Management**: Real-time task tracking with status updates
- **Credit System**: Purchase credits via Razorpay integration
- **Dashboard**: Comprehensive user dashboard with task history and credit balance
- **Responsive Design**: Mobile-first design that works on all devices

### Admin Features
- **User Management**: View and manage all users
- **Task Analytics**: Real-time task statistics and monitoring
- **Credit Management**: Track credit purchases and usage
- **Dashboard Analytics**: Visual charts and metrics

## 🛠️ Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS + Shadcn/ui
- **State Management**: React Context + SWR
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **File Upload**: React Dropzone
- **Payments**: Razorpay
- **Icons**: Lucide React
- **Notifications**: Sonner

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- Access to the Virtual Space Tech Backend API
- Razorpay account (for payments)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd virtual-space-tech-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   ```
   
   Update `.env.local` with your configuration:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_RAZORPAY_KEY_ID=your_razorpay_key_id
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── admin/             # Admin panel page
│   ├── dashboard/         # User dashboard
│   ├── login/             # Login page
│   ├── signup/            # Registration page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── ui/               # Shadcn/ui components
│   ├── Header.tsx        # Navigation header
│   ├── ImageUpload.tsx   # File upload component
│   ├── TaskList.tsx      # Task management
│   └── CreditPurchase.tsx # Payment integration
├── contexts/             # React contexts
│   └── AuthContext.tsx   # Authentication state
├── hooks/                # Custom hooks
│   └── useApi.ts         # SWR data fetching hooks
├── lib/                  # Utilities and configurations
│   ├── api/              # API integration
│   └── utils.ts          # Helper functions
└── types/                # TypeScript type definitions
    └── api.ts            # API response types
```

## 🔌 API Integration

The frontend integrates with the Virtual Space Tech Backend API. Make sure the backend is running and accessible at the URL specified in `NEXT_PUBLIC_API_URL`.

### API Endpoints Used
- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `POST /tasks/` - Create new image processing task
- `GET /tasks/` - Get user tasks
- `GET /tasks/{task_id}` - Get specific task details
- `POST /credits/purchase` - Purchase credits
- `GET /credits/balance` - Get credit balance
- `GET /admin/users` - Admin: Get all users
- `GET /admin/tasks` - Admin: Get all tasks
- `GET /admin/analytics` - Admin: Get analytics data

## 🎨 UI Components

The project uses Shadcn/ui components for consistent design:

- **Form Components**: Button, Input, Textarea, Select, Label
- **Layout**: Card, Separator, Tabs
- **Feedback**: Badge, Progress, Dialog, Sonner (toasts)
- **Data Display**: Table, Avatar
- **Navigation**: Dropdown Menu

## 🔒 Authentication

- JWT-based authentication with automatic token refresh
- Protected routes with role-based access control
- Persistent login state with cookies
- Automatic logout on token expiration

## 💳 Payment Integration

- Razorpay integration for credit purchases
- Dynamic script loading for optimal performance
- Error handling and success feedback
- Support for multiple payment methods

## 📱 Responsive Design

- Mobile-first approach
- Responsive navigation with mobile menu
- Optimized layouts for all screen sizes
- Touch-friendly interactions

## 🚀 Deployment

### Production Build
```bash
npm run build
npm start
```

### Docker Support
```bash
# Build Docker image
docker build -t virtual-space-tech-frontend .

# Run container
docker run -p 3000:3000 virtual-space-tech-frontend
```

### Environment Variables for Production
```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_RAZORPAY_KEY_ID=your_production_razorpay_key
```

## 📊 Performance Optimization

- Next.js Image optimization
- Lazy loading for components
- SWR for efficient data fetching
- Code splitting with dynamic imports
- Optimized bundle size

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## 🔗 Links

- [Backend Repository](link-to-backend-repo)
- [API Documentation](link-to-api-docs)
- [Design System](link-to-design-docs)
- [Live Demo](link-to-demo)
