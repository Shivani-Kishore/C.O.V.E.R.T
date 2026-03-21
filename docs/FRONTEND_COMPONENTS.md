# C.O.V.E.R.T Frontend Components Specification

## Overview

This document defines the complete component architecture for the C.O.V.E.R.T React frontend application, including UI components, state management, routing structure, and design patterns.

## Tech Stack

- **Framework**: React 18.2+ with TypeScript
- **Build Tool**: Vite 4.x
- **Styling**: TailwindCSS 3.x
- **State Management**: Zustand + React Query
- **Routing**: React Router v6
- **Web3**: ethers.js v6
- **Forms**: React Hook Form + Zod
- **UI Components**: Headless UI + Custom components
- **Icons**: Heroicons
- **Notifications**: React Hot Toast

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Shared components
│   │   ├── reporter/       # Reporter-specific components
│   │   ├── moderator/      # Moderator-specific components
│   │   └── layout/         # Layout components
│   ├── pages/              # Route pages
│   ├── services/           # API and blockchain services
│   ├── hooks/              # Custom React hooks
│   ├── store/              # Zustand stores
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript types
│   ├── constants/          # App constants
│   ├── styles/             # Global styles
│   └── App.tsx             # Root component
├── public/
└── package.json
```

## Design System

### Color Palette

```typescript
// tailwind.config.js
export const colors = {
  primary: {
    50: '#f0f9ff',
    100: '#e0f2fe',
    200: '#bae6fd',
    300: '#7dd3fc',
    400: '#38bdf8',
    500: '#0ea5e9',  // Main brand color
    600: '#0284c7',
    700: '#0369a1',
    800: '#075985',
    900: '#0c4a6e',
  },
  danger: {
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  },
  success: {
    500: '#10b981',
    600: '#059669',
  },
  warning: {
    500: '#f59e0b',
    600: '#d97706',
  },
  neutral: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#e5e5e5',
    300: '#d4d4d4',
    400: '#a3a3a3',
    500: '#737373',
    600: '#525252',
    700: '#404040',
    800: '#262626',
    900: '#171717',
  }
}
```

### Typography

```typescript
export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  }
}
```

### Spacing

```typescript
// Using Tailwind's default spacing scale (0.25rem increments)
// Common patterns:
// - Card padding: p-6 (1.5rem)
// - Section spacing: space-y-8 (2rem)
// - Button padding: px-4 py-2
```

## Component Library

### 1. Common Components

#### Button Component

```typescript
// components/common/Button.tsx
import { ButtonHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
}

export const Button = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) => {
  const baseStyles = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
    secondary: 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus:ring-neutral-500',
    danger: 'bg-danger-600 text-white hover:bg-danger-700 focus:ring-danger-500',
    ghost: 'text-neutral-700 hover:bg-neutral-100 focus:ring-neutral-500',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button
      className={clsx(
        baseStyles,
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <LoadingSpinner size={size} />
      ) : (
        <>
          {leftIcon && <span className="mr-2">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="ml-2">{rightIcon}</span>}
        </>
      )}
    </button>
  );
};
```

#### Input Component

```typescript
// components/common/Input.tsx
import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            className={clsx(
              'block w-full px-4 py-2 border rounded-lg',
              'focus:ring-2 focus:ring-primary-500 focus:border-transparent',
              'transition-colors',
              error 
                ? 'border-danger-500 text-danger-900' 
                : 'border-neutral-300 text-neutral-900',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              props.disabled && 'bg-neutral-100 cursor-not-allowed',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-1 text-sm text-danger-600">{error}</p>
        )}
        {helperText && !error && (
          <p className="mt-1 text-sm text-neutral-500">{helperText}</p>
        )}
      </div>
    );
  }
);
```

#### Card Component

```typescript
// components/common/Card.tsx
interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export const Card = ({ 
  children, 
  className, 
  padding = 'md',
  hover = false 
}: CardProps) => {
  const paddings = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };
  
  return (
    <div className={clsx(
      'bg-white rounded-lg border border-neutral-200 shadow-sm',
      paddings[padding],
      hover && 'hover:shadow-md transition-shadow',
      className
    )}>
      {children}
    </div>
  );
};
```

#### Modal Component

```typescript
// components/common/Modal.tsx
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showCloseButton?: boolean;
}

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
}: ModalProps) => {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };
  
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className={clsx(
                'w-full transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all',
                sizes[size]
              )}>
                {(title || showCloseButton) && (
                  <div className="flex items-center justify-between mb-4">
                    {title && (
                      <Dialog.Title className="text-lg font-semibold text-neutral-900">
                        {title}
                      </Dialog.Title>
                    )}
                    {showCloseButton && (
                      <button
                        onClick={onClose}
                        className="text-neutral-400 hover:text-neutral-600"
                      >
                        <XMarkIcon className="h-6 w-6" />
                      </button>
                    )}
                  </div>
                )}
                {children}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};
```

#### LoadingSpinner Component

```typescript
// components/common/LoadingSpinner.tsx
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner = ({ size = 'md', className }: LoadingSpinnerProps) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };
  
  return (
    <div className={clsx('animate-spin rounded-full border-2 border-neutral-300 border-t-primary-600', sizes[size], className)} />
  );
};
```

### 2. Layout Components

#### AppLayout Component

```typescript
// components/layout/AppLayout.tsx
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';

export const AppLayout = () => {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
      <Footer />
    </div>
  );
};
```

#### Header Component

```typescript
// components/layout/Header.tsx
import { useAuth } from '@/hooks/useAuth';
import { WalletButton } from '@/components/common/WalletButton';
import { NotificationBell } from '@/components/common/NotificationBell';
import { ShieldCheckIcon } from '@heroicons/react/24/outline';

export const Header = () => {
  const { isAuthenticated, user } = useAuth();
  
  return (
    <header className="bg-white border-b border-neutral-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <ShieldCheckIcon className="h-8 w-8 text-primary-600" />
            <span className="ml-2 text-xl font-bold text-neutral-900">
              C.O.V.E.R.T
            </span>
          </div>
          
          {/* Right section */}
          <div className="flex items-center space-x-4">
            {isAuthenticated && <NotificationBell />}
            <WalletButton />
          </div>
        </div>
      </div>
    </header>
  );
};
```

#### Sidebar Component

```typescript
// components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import {
  HomeIcon,
  DocumentPlusIcon,
  ClipboardDocumentListIcon,
  ShieldExclamationIcon,
  ChartBarIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

export const Sidebar = () => {
  const { role } = useAuth();
  
  const reporterLinks = [
    { to: '/dashboard', icon: HomeIcon, label: 'Dashboard' },
    { to: '/submit', icon: DocumentPlusIcon, label: 'Submit Report' },
    { to: '/my-reports', icon: ClipboardDocumentListIcon, label: 'My Reports' },
    { to: '/settings', icon: Cog6ToothIcon, label: 'Settings' },
  ];
  
  const moderatorLinks = [
    { to: '/moderator/dashboard', icon: HomeIcon, label: 'Dashboard' },
    { to: '/moderator/queue', icon: ClipboardDocumentListIcon, label: 'Review Queue' },
    { to: '/moderator/disputes', icon: ShieldExclamationIcon, label: 'Disputes' },
    { to: '/moderator/analytics', icon: ChartBarIcon, label: 'Analytics' },
  ];
  
  const links = role === 'moderator' ? moderatorLinks : reporterLinks;
  
  return (
    <aside className="w-64 bg-white border-r border-neutral-200 hidden md:block">
      <nav className="p-4 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center px-4 py-3 rounded-lg transition-colors',
                isActive
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-neutral-600 hover:bg-neutral-100'
              )
            }
          >
            <link.icon className="h-5 w-5 mr-3" />
            <span className="font-medium">{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};
```

### 3. Reporter Components

#### ReportSubmissionForm Component

```typescript
// components/reporter/ReportSubmissionForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useState } from 'react';
import { useEncryption } from '@/hooks/useEncryption';
import { useIPFS } from '@/hooks/useIPFS';
import { useSmartContract } from '@/hooks/useSmartContract';

const reportSchema = z.object({
  category: z.enum(['corruption', 'fraud', 'safety', 'environment', 'human_rights', 'other']),
  title: z.string().min(10).max(200),
  description: z.string().min(50).max(5000),
  visibility: z.enum(['private', 'moderated', 'public']),
  attachments: z.array(z.instanceof(File)).max(5),
});

type ReportFormData = z.infer<typeof reportSchema>;

export const ReportSubmissionForm = () => {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { encrypt } = useEncryption();
  const { uploadToIPFS } = useIPFS();
  const { submitCommitment } = useSmartContract();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ReportFormData>({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      visibility: 'moderated',
    },
  });
  
  const onSubmit = async (data: ReportFormData) => {
    setIsSubmitting(true);
    try {
      // Step 1: Encrypt data
      const encryptedData = await encrypt({
        title: data.title,
        description: data.description,
        category: data.category,
      });
      
      // Step 2: Upload to IPFS
      const ipfsCID = await uploadToIPFS(encryptedData);
      
      // Step 3: Submit commitment to blockchain
      const txHash = await submitCommitment(ipfsCID);
      
      // Step 4: Submit to backend
      await submitReport({
        ipfsCID,
        txHash,
        visibility: data.visibility,
      });
      
      toast.success('Report submitted successfully!');
      navigate('/my-reports');
    } catch (error) {
      toast.error('Failed to submit report');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Step Indicator */}
        <StepIndicator currentStep={step} totalSteps={3} />
        
        {step === 1 && (
          <>
            <h2 className="text-2xl font-bold">Report Details</h2>
            
            <Select
              label="Category"
              {...register('category')}
              error={errors.category?.message}
            >
              <option value="">Select a category</option>
              <option value="corruption">Corruption</option>
              <option value="fraud">Fraud</option>
              <option value="safety">Safety Violation</option>
              <option value="environment">Environmental</option>
              <option value="human_rights">Human Rights</option>
              <option value="other">Other</option>
            </Select>
            
            <Input
              label="Title"
              placeholder="Brief summary of the issue"
              {...register('title')}
              error={errors.title?.message}
            />
            
            <Textarea
              label="Description"
              placeholder="Provide detailed information..."
              rows={8}
              {...register('description')}
              error={errors.description?.message}
            />
            
            <Button onClick={() => setStep(2)}>Next: Attachments</Button>
          </>
        )}
        
        {step === 2 && (
          <>
            <h2 className="text-2xl font-bold">Attachments (Optional)</h2>
            
            <FileUpload
              {...register('attachments')}
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              maxFiles={5}
              maxSize={10 * 1024 * 1024} // 10MB
            />
            
            <div className="flex space-x-4">
              <Button variant="secondary" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={() => setStep(3)}>Next: Privacy Settings</Button>
            </div>
          </>
        )}
        
        {step === 3 && (
          <>
            <h2 className="text-2xl font-bold">Privacy Settings</h2>
            
            <RadioGroup
              label="Report Visibility"
              {...register('visibility')}
            >
              <Radio value="private" label="Private" description="Only you can see this report" />
              <Radio value="moderated" label="Moderated" description="Visible to moderators only" />
              <Radio value="public" label="Public" description="Visible to everyone after verification" />
            </RadioGroup>
            
            <Alert variant="info">
              Your identity is protected through zero-knowledge proofs. Even moderators cannot see who submitted this report.
            </Alert>
            
            <div className="flex space-x-4">
              <Button variant="secondary" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button type="submit" isLoading={isSubmitting}>
                Submit Report
              </Button>
            </div>
          </>
        )}
      </form>
    </Card>
  );
};
```

#### ReportCard Component

```typescript
// components/reporter/ReportCard.tsx
interface ReportCardProps {
  report: Report;
  onClick?: () => void;
}

export const ReportCard = ({ report, onClick }: ReportCardProps) => {
  return (
    <Card hover className="cursor-pointer" onClick={onClick}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <Badge variant={getStatusVariant(report.status)}>
              {report.status}
            </Badge>
            <Badge variant="outline">{report.category}</Badge>
          </div>
          <h3 className="text-lg font-semibold text-neutral-900 mb-1">
            {report.encrypted_title ? '••••••••••' : 'Report #' + report.id.slice(0, 8)}
          </h3>
          <p className="text-sm text-neutral-600">
            Submitted {formatDate(report.submission_timestamp)}
          </p>
        </div>
        
        {report.verification_score && (
          <div className="flex flex-col items-end">
            <span className="text-sm text-neutral-600">Credibility</span>
            <span className="text-2xl font-bold text-primary-600">
              {(report.verification_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
      
      <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
        <div className="flex items-center text-sm text-neutral-600">
          <ShieldCheckIcon className="h-4 w-4 mr-1" />
          <span>On-chain verified</span>
        </div>
        
        <ChevronRightIcon className="h-5 w-5 text-neutral-400" />
      </div>
    </Card>
  );
};
```

#### ReportDetailView Component

```typescript
// components/reporter/ReportDetailView.tsx
interface ReportDetailViewProps {
  reportId: string;
}

export const ReportDetailView = ({ reportId }: ReportDetailViewProps) => {
  const { data: report, isLoading } = useQuery(['report', reportId], () => 
    fetchReport(reportId)
  );
  
  if (isLoading) return <LoadingSpinner />;
  if (!report) return <div>Report not found</div>;
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900 mb-2">
              Report Details
            </h1>
            <p className="text-neutral-600">
              ID: {report.id}
            </p>
          </div>
          <Badge variant={getStatusVariant(report.status)} size="lg">
            {report.status}
          </Badge>
        </div>
      </Card>
      
      {/* Timeline */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Report Timeline</h2>
        <ReportTimeline events={report.logs} />
      </Card>
      
      {/* Blockchain Info */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Blockchain Verification</h2>
        <div className="space-y-2">
          <InfoRow label="Transaction Hash" value={report.transaction_hash} copyable />
          <InfoRow label="Block Number" value={report.block_number} />
          <InfoRow label="IPFS CID" value={report.ipfs_cid} copyable />
          <InfoRow label="Commitment Hash" value={report.commitment_hash} copyable />
        </div>
      </Card>
      
      {/* Actions */}
      <div className="flex space-x-4">
        <Button variant="secondary">Download Proof</Button>
        <Button variant="secondary">View on Explorer</Button>
        {report.status === 'pending' && (
          <Button variant="danger">Withdraw Report</Button>
        )}
      </div>
    </div>
  );
};
```

### 4. Moderator Components

#### ModerationQueue Component

```typescript
// components/moderator/ModerationQueue.tsx
export const ModerationQueue = () => {
  const [filter, setFilter] = useState<'all' | 'pending' | 'high_risk'>('all');
  const { data: reports, isLoading } = useQuery(
    ['moderation-queue', filter],
    () => fetchModerationQueue(filter)
  );
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Moderation Queue</h1>
        
        <div className="flex space-x-2">
          <Button
            variant={filter === 'all' ? 'primary' : 'ghost'}
            onClick={() => setFilter('all')}
          >
            All Reports
          </Button>
          <Button
            variant={filter === 'pending' ? 'primary' : 'ghost'}
            onClick={() => setFilter('pending')}
          >
            Pending
          </Button>
          <Button
            variant={filter === 'high_risk' ? 'primary' : 'ghost'}
            onClick={() => setFilter('high_risk')}
          >
            High Risk
          </Button>
        </div>
      </div>
      
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid gap-4">
          {reports?.map((report) => (
            <ModerationReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  );
};
```

#### ModerationReportCard Component

```typescript
// components/moderator/ModerationReportCard.tsx
interface ModerationReportCardProps {
  report: Report;
}

export const ModerationReportCard = ({ report }: ModerationReportCardProps) => {
  const [isReviewing, setIsReviewing] = useState(false);
  
  return (
    <Card>
      <div className="flex justify-between">
        <div className="flex-1 space-y-4">
          <div className="flex items-center space-x-3">
            <Badge variant="outline">{report.category}</Badge>
            <span className="text-sm text-neutral-600">
              Submitted {formatDistanceToNow(report.submission_timestamp)} ago
            </span>
            {report.risk_level && (
              <Badge variant={getRiskVariant(report.risk_level)}>
                {report.risk_level} Risk
              </Badge>
            )}
          </div>
          
          {/* AI Recommendation */}
          {report.ai_recommendation && (
            <Alert variant="info">
              <SparklesIcon className="h-5 w-5" />
              <div>
                <p className="font-medium">AI Recommendation: {report.ai_recommendation}</p>
                <p className="text-sm">Confidence: {(report.ai_confidence * 100).toFixed(0)}%</p>
              </div>
            </Alert>
          )}
          
          {/* Metadata Preview */}
          <div className="bg-neutral-50 p-4 rounded-lg">
            <p className="text-sm text-neutral-600 mb-1">Category: {report.encrypted_category}</p>
            <p className="text-sm text-neutral-600">File Size: {formatBytes(report.file_size)}</p>
            <p className="text-sm text-neutral-600">IPFS CID: {report.ipfs_cid}</p>
          </div>
        </div>
        
        <div className="ml-6 flex flex-col space-y-2">
          <Button onClick={() => setIsReviewing(true)}>
            Review Report
          </Button>
          <Button variant="secondary">Skip</Button>
          <Button variant="danger">Flag for Review</Button>
        </div>
      </div>
      
      {isReviewing && (
        <ModerationModal
          report={report}
          isOpen={isReviewing}
          onClose={() => setIsReviewing(false)}
        />
      )}
    </Card>
  );
};
```

#### ModerationModal Component

```typescript
// components/moderator/ModerationModal.tsx
interface ModerationModalProps {
  report: Report;
  isOpen: boolean;
  onClose: () => void;
}

export const ModerationModal = ({ report, isOpen, onClose }: ModerationModalProps) => {
  const [decision, setDecision] = useState<'accept' | 'reject' | 'need_info'>('accept');
  const [notes, setNotes] = useState('');
  const { mutate: submitDecision, isLoading } = useMutation(submitModerationDecision);
  
  const handleSubmit = () => {
    submitDecision({
      reportId: report.id,
      decision,
      notes,
    }, {
      onSuccess: () => {
        toast.success('Decision submitted successfully');
        onClose();
      }
    });
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" title="Review Report">
      <div className="space-y-6">
        {/* Report Info */}
        <div className="bg-neutral-50 p-4 rounded-lg space-y-2">
          <InfoRow label="Report ID" value={report.id} />
          <InfoRow label="Category" value={report.category} />
          <InfoRow label="Submitted" value={formatDate(report.submission_timestamp)} />
          <InfoRow label="Credibility Score" value={`${(report.verification_score * 100).toFixed(0)}%`} />
        </div>
        
        {/* Decision */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-2">
            Your Decision
          </label>
          <div className="flex space-x-4">
            <Button
              variant={decision === 'accept' ? 'primary' : 'ghost'}
              onClick={() => setDecision('accept')}
              leftIcon={<CheckIcon className="h-5 w-5" />}
            >
              Accept
            </Button>
            <Button
              variant={decision === 'reject' ? 'danger' : 'ghost'}
              onClick={() => setDecision('reject')}
              leftIcon={<XMarkIcon className="h-5 w-5" />}
            >
              Reject
            </Button>
            <Button
              variant={decision === 'need_info' ? 'primary' : 'ghost'}
              onClick={() => setDecision('need_info')}
              leftIcon={<QuestionMarkCircleIcon className="h-5 w-5" />}
            >
              Need More Info
            </Button>
          </div>
        </div>
        
        {/* Notes */}
        <Textarea
          label="Moderator Notes (Encrypted)"
          placeholder="Explain your decision..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={4}
        />
        
        {/* Actions */}
        <div className="flex justify-end space-x-4">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} isLoading={isLoading}>
            Submit Decision
          </Button>
        </div>
      </div>
    </Modal>
  );
};
```

### 5. Web3 Components

#### WalletButton Component

```typescript
// components/common/WalletButton.tsx
import { useWallet } from '@/hooks/useWallet';
import { Menu } from '@headlessui/react';

export const WalletButton = () => {
  const { address, isConnected, connect, disconnect, balance } = useWallet();
  
  if (!isConnected) {
    return (
      <Button onClick={connect} leftIcon={<WalletIcon className="h-5 w-5" />}>
        Connect Wallet
      </Button>
    );
  }
  
  return (
    <Menu as="div" className="relative">
      <Menu.Button as={Button} variant="secondary">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 bg-green-500 rounded-full" />
          <span>{formatAddress(address)}</span>
        </div>
      </Menu.Button>
      
      <Menu.Items className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-neutral-200 p-2">
        <div className="px-4 py-3 border-b border-neutral-200">
          <p className="text-sm text-neutral-600">Balance</p>
          <p className="text-lg font-semibold">{balance} MATIC</p>
        </div>
        
        <Menu.Item>
          {({ active }) => (
            <button
              className={clsx(
                'w-full text-left px-4 py-2 rounded-md',
                active && 'bg-neutral-100'
              )}
              onClick={() => navigator.clipboard.writeText(address)}
            >
              Copy Address
            </button>
          )}
        </Menu.Item>
        
        <Menu.Item>
          {({ active }) => (
            <button
              className={clsx(
                'w-full text-left px-4 py-2 rounded-md text-danger-600',
                active && 'bg-danger-50'
              )}
              onClick={disconnect}
            >
              Disconnect
            </button>
          )}
        </Menu.Item>
      </Menu.Items>
    </Menu>
  );
};
```

## State Management

### Zustand Stores

#### Auth Store

```typescript
// store/authStore.ts
import create from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  isAuthenticated: boolean;
  address: string | null;
  role: 'reporter' | 'moderator' | null;
  sessionToken: string | null;
  login: (address: string, role: 'reporter' | 'moderator', token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      address: null,
      role: null,
      sessionToken: null,
      login: (address, role, token) =>
        set({ isAuthenticated: true, address, role, sessionToken: token }),
      logout: () =>
        set({ isAuthenticated: false, address: null, role: null, sessionToken: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

#### Wallet Store

```typescript
// store/walletStore.ts
import create from 'zustand';

interface WalletState {
  address: string | null;
  chainId: number | null;
  balance: string;
  isConnected: boolean;
  setWallet: (address: string, chainId: number) => void;
  setBalance: (balance: string) => void;
  disconnect: () => void;
}

export const useWalletStore = create<WalletState>((set) => ({
  address: null,
  chainId: null,
  balance: '0',
  isConnected: false,
  setWallet: (address, chainId) =>
    set({ address, chainId, isConnected: true }),
  setBalance: (balance) => set({ balance }),
  disconnect: () =>
    set({ address: null, chainId: null, balance: '0', isConnected: false }),
}));
```

## Routing Structure

```typescript
// App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Reporter Routes */}
        <Route element={<ProtectedRoute role="reporter" />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<ReporterDashboard />} />
            <Route path="/submit" element={<SubmitReportPage />} />
            <Route path="/my-reports" element={<MyReportsPage />} />
            <Route path="/report/:id" element={<ReportDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>
        
        {/* Moderator Routes */}
        <Route element={<ProtectedRoute role="moderator" />}>
          <Route element={<AppLayout />}>
            <Route path="/moderator/dashboard" element={<ModeratorDashboard />} />
            <Route path="/moderator/queue" element={<ModerationQueuePage />} />
            <Route path="/moderator/disputes" element={<DisputesPage />} />
            <Route path="/moderator/analytics" element={<AnalyticsPage />} />
          </Route>
        </Route>
        
        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Performance Optimization

### Code Splitting

```typescript
import { lazy, Suspense } from 'react';

const ReportDetailPage = lazy(() => import('./pages/ReportDetailPage'));
const ModerationQueuePage = lazy(() => import('./pages/ModerationQueuePage'));

// Usage
<Suspense fallback={<LoadingSpinner />}>
  <ReportDetailPage />
</Suspense>
```

### Memoization

```typescript
import { memo, useMemo, useCallback } from 'react';

export const ReportCard = memo(({ report }: ReportCardProps) => {
  const formattedDate = useMemo(
    () => formatDate(report.submission_timestamp),
    [report.submission_timestamp]
  );
  
  const handleClick = useCallback(() => {
    navigate(`/report/${report.id}`);
  }, [report.id]);
  
  return (
    // Component JSX
  );
});
```

## Testing Strategy

### Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('shows loading spinner when isLoading is true', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

---

This component specification provides a complete blueprint for building the C.O.V.E.R.T frontend. All components follow React and TypeScript best practices with proper typing, accessibility, and performance optimization.
