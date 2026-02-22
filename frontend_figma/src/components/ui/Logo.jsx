export const Logo = ({ size = 'default', showText = true }) => {
  const sizes = {
    small: { fish: 24, text: 'text-xl' },
    default: { fish: 32, text: 'text-2xl' },
    large: { fish: 48, text: 'text-4xl' },
  };

  const { fish: fishSize, text: textSize } = sizes[size];

  return (
    <div className="flex items-center gap-2">
      {/* Tuna Fish SVG Icon */}
      <svg
        width={fishSize}
        height={fishSize}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        {/* Simple geometric tuna silhouette */}
        <path
          d="M8 20 C8 20, 2 18, 2 20 C2 22, 8 20, 8 20 M8 20 C8 20, 12 10, 28 12 C32 12.5, 35 15, 36 18 C37 21, 36 24, 34 26 C32 28, 28 28, 24 27.5 C12 26, 8 20, 8 20 M28 12 L32 8 M28 12 L30 6 M24 27.5 L26 32 M24 27.5 L28 30 M28 18 C28 18.5, 27.5 19, 27 19 C26.5 19, 26 18.5, 26 18 C26 17.5, 26.5 17, 27 17 C27.5 17, 28 17.5, 28 18"
          stroke="#4059AD"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="#4059AD"
          fillOpacity="0.9"
        />
      </svg>
      
      {showText && (
        <span className={`${textSize} font-bold tracking-tight`} style={{ fontFamily: 'var(--font-logo)' }}>
          <span style={{ color: '#4059AD' }}>Tuna</span>
          <span style={{ color: '#000000' }}>Tax</span>
        </span>
      )}
    </div>
  );
};
