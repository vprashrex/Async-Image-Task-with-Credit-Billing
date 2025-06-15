'use client';

import { useEffect } from 'react';

interface AccessibilityConfig {
  enableAnnouncements?: boolean;
  enableKeyboardNavigation?: boolean;
  enableFocusManagement?: boolean;
  enableAriaLabels?: boolean;
}

export function useAccessibility(config: AccessibilityConfig = {}) {
  const {
    enableAnnouncements = true,
    enableKeyboardNavigation = true,
    enableFocusManagement = true,
    enableAriaLabels = true,
  } = config;

  useEffect(() => {
    if (enableKeyboardNavigation) {
      // Handle skip links
      const skipLink = document.querySelector('[data-skip-link]');
      if (skipLink) {
        skipLink.addEventListener('click', (e) => {
          e.preventDefault();
          const target = document.querySelector('#main-content');
          if (target) {
            (target as HTMLElement).focus();
          }
        });
      }

      // Handle keyboard navigation for custom components
      const handleKeyDown = (e: KeyboardEvent) => {
        // ESC to close modals/dropdowns
        if (e.key === 'Escape') {
          const activeModal = document.querySelector('[role="dialog"][aria-hidden="false"]');
          if (activeModal) {
            const closeButton = activeModal.querySelector('[aria-label*="close"], [data-dismiss]');
            if (closeButton) {
              (closeButton as HTMLElement).click();
            }
          }
        }

        // Arrow keys for navigation in lists/grids
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
          const activeElement = document.activeElement;
          if (activeElement?.getAttribute('role') === 'menuitem') {
            handleMenuNavigation(e, activeElement as HTMLElement);
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [enableKeyboardNavigation]);

  useEffect(() => {
    if (enableFocusManagement) {
      // Manage focus for dynamic content
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList') {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                const element = node as Element;
                
                // Auto-focus first focusable element in new content
                if (element.matches('[role="dialog"], .modal')) {
                  const firstFocusable = element.querySelector(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                  );
                  if (firstFocusable) {
                    setTimeout(() => (firstFocusable as HTMLElement).focus(), 100);
                  }
                }
              }
            });
          }
        });
      });

      observer.observe(document.body, { childList: true, subtree: true });
      return () => observer.disconnect();
    }
  }, [enableFocusManagement]);

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!enableAnnouncements) return;

    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', priority);
    announcer.setAttribute('aria-atomic', 'true');
    announcer.setAttribute('class', 'sr-only');
    announcer.textContent = message;

    document.body.appendChild(announcer);

    setTimeout(() => {
      document.body.removeChild(announcer);
    }, 1000);
  };

  return { announce };
}

function handleMenuNavigation(e: KeyboardEvent, activeElement: HTMLElement) {
  const menu = activeElement.closest('[role="menu"]');
  if (!menu) return;

  const menuItems = Array.from(menu.querySelectorAll('[role="menuitem"]')) as HTMLElement[];
  const currentIndex = menuItems.indexOf(activeElement);

  let nextIndex = currentIndex;

  switch (e.key) {
    case 'ArrowDown':
      nextIndex = (currentIndex + 1) % menuItems.length;
      break;
    case 'ArrowUp':
      nextIndex = currentIndex === 0 ? menuItems.length - 1 : currentIndex - 1;
      break;
    case 'Home':
      nextIndex = 0;
      break;
    case 'End':
      nextIndex = menuItems.length - 1;
      break;
    default:
      return;
  }

  e.preventDefault();
  menuItems[nextIndex]?.focus();
}

// Component for skip links
export function SkipLink({ href = '#main-content', children = 'Skip to main content' }) {
  return (
    <a
      href={href}
      data-skip-link
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:font-medium"
    >
      {children}
    </a>
  );
}

// Screen reader only text component
export function ScreenReaderOnly({ children, ...props }: React.HTMLProps<HTMLSpanElement>) {
  return (
    <span className="sr-only" {...props}>
      {children}
    </span>
  );
}

// Accessible form field component
interface AccessibleFieldProps {
  id: string;
  label: string;
  error?: string;
  description?: string;
  required?: boolean;
  children: React.ReactElement;
}

export function AccessibleField({
  id,
  label,
  error,
  description,
  required,
  children,
}: AccessibleFieldProps) {
  const descriptionId = description ? `${id}-description` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  
  const ariaDescribedBy = [descriptionId, errorId].filter(Boolean).join(' ') || undefined;

  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
        {required && (
          <span className="text-destructive ml-1" aria-label="required">
            *
          </span>
        )}
      </label>
      
      {description && (
        <p id={descriptionId} className="text-sm text-muted-foreground">
          {description}
        </p>
      )}
      
      {React.cloneElement(children, {
        id,
        'aria-describedby': ariaDescribedBy,
        'aria-invalid': error ? 'true' : undefined,
        'aria-required': required,
      })}
      
      {error && (
        <p id={errorId} role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
