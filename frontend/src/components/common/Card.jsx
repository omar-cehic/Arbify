import React from 'react';

/**
 * Card component for displaying content in a boxed container
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Card content
 * @param {string} [props.title] - Card title
 * @param {string} [props.variant='default'] - Card variant (default, highlighted)
 * @param {boolean} [props.hoverable=false] - Whether card should have hover effect
 * @param {string} [props.className=''] - Additional CSS classes
 * @returns {JSX.Element} Card component
 */
const Card = ({ 
  children, 
  title, 
  variant = 'default', 
  hoverable = false,
  className = '',
  ...props 
}) => {
  // Base classes for all cards
  const baseClasses = 'rounded-lg border p-5';
  
  // Variant classes
  const variantClasses = {
    default: 'bg-gray-800 border-gray-700',
    highlighted: 'bg-gray-700 border-yellow-400/50',
    dark: 'bg-gray-900 border-gray-800'
  };
  
  // Hover class
  const hoverClass = hoverable ? 'transition-shadow hover:shadow-lg' : '';
  
  return (
    <div 
      className={`${baseClasses} ${variantClasses[variant]} ${hoverClass} ${className}`}
      {...props}
    >
      {title && (
        <h3 className="text-lg font-bold text-white mb-3">{title}</h3>
      )}
      {children}
    </div>
  );
};

export default Card; 