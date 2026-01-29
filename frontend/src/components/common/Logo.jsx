import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * Logo component with consistent styling across the application
 * Includes SVG fallback for reliable rendering
 */
const Logo = ({ size = 'md', className = '', variant = 'default' }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [error, setError] = useState(false);

  // Size variants
  const sizes = {
    sm: { height: '32px', fontSize: '16px' },
    md: { height: '40px', fontSize: '20px' },
    lg: { height: '64px', fontSize: '28px' },
    xl: { height: '96px', fontSize: '36px' }
  };

  const style = sizes[size] || sizes.md;

  // SVG fallback logo - guaranteed to display correctly
  const renderSvgLogo = () => (
    <div 
      className={`inline-flex items-center justify-center bg-yellow-500 text-black font-bold ${className}`}
      style={{
        height: style.height,
        padding: '0.5rem 1rem',
        borderRadius: '4px',
        fontSize: style.fontSize,
        fontWeight: 'bold',
        letterSpacing: '1px'
      }}
    >
      ARBIFY
    </div>
  );

  // Only attempt to load the image if we're using the default variant
  if (variant === 'svg' || error) {
    return renderSvgLogo();
  }

  return (
    <>
      {!imageLoaded && (
        <div className={`inline-block ${className}`} style={{ height: style.height }}>
          {renderSvgLogo()}
        </div>
      )}
      <img 
        src="/images/arbify-logo.png" 
        alt="Arbify Logo" 
        className={`${!imageLoaded ? 'hidden' : ''} ${className}`}
        style={{ height: style.height }}
        onLoad={() => setImageLoaded(true)}
        onError={(e) => {
          console.log("Logo loading failed, using SVG fallback");
          setError(true);
        }}
      />
    </>
  );
};

Logo.propTypes = {
  size: PropTypes.oneOf(['sm', 'md', 'lg', 'xl']),
  className: PropTypes.string,
  variant: PropTypes.oneOf(['default', 'svg'])
};

export default Logo; 