import { motion } from 'motion/react';

const FishSVG = ({ size = 40, opacity = 0.7 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 40 40"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M8 20 C8 20, 2 18, 2 20 C2 22, 8 20, 8 20 M8 20 C8 20, 12 10, 28 12 C32 12.5, 35 15, 36 18 C37 21, 36 24, 34 26 C32 28, 28 28, 24 27.5 C12 26, 8 20, 8 20 M28 12 L32 8 M28 12 L30 6 M24 27.5 L26 32 M24 27.5 L28 30 M28 18 C28 18.5, 27.5 19, 27 19 C26.5 19, 26 18.5, 26 18 C26 17.5, 26.5 17, 27 17 C27.5 17, 28 17.5, 28 18"
      stroke="#4059AD"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="#4059AD"
      fillOpacity={opacity}
    />
  </svg>
);

const Fish = ({ index, direction = 'right' }) => {
  const sizes = [25, 30, 35, 40, 45, 50];
  const size = sizes[index % sizes.length];
  
  const startY = 10 + (index * 60) % 80;
  const startX = direction === 'right' ? -50 : 120;
  const endX = direction === 'right' ? 120 : -50;
  
  const hopDuration = 3 + (index % 3);
  const delay = index * 0.8;
  
  const scaleX = direction === 'right' ? 1 : -1;

  return (
    <motion.div
      className="absolute"
      style={{
        top: `${startY}%`,
        left: `${startX}%`,
        scaleX,
      }}
      initial={{ x: 0, y: 0, opacity: 0.3 }}
      animate={{
        x: [`0%`, `${(endX - startX) * 0.25}%`, `${(endX - startX) * 0.5}%`, `${(endX - startX) * 0.75}%`, `${endX - startX}%`],
        y: ['0px', '-60px', '-80px', '-50px', '0px'],
        rotate: [0, -15, -5, 10, 0],
        opacity: [0.3, 0.7, 0.9, 0.8, 0.3],
      }}
      transition={{
        duration: hopDuration,
        delay,
        repeat: Infinity,
        repeatDelay: 1,
        ease: 'easeInOut',
      }}
    >
      <FishSVG size={size} opacity={0.4 + (index % 3) * 0.15} />
    </motion.div>
  );
};

export const FishAnimation = () => {
  const fishCount = 10;
  const fishes = Array.from({ length: fishCount }, (_, i) => ({
    index: i,
    direction: i % 2 === 0 ? 'right' : 'left',
  }));

  return (
    <div className="relative w-full h-64 overflow-hidden">
      {/* Water ripple effect at bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-16 opacity-20">
        <svg width="100%" height="100%" viewBox="0 0 1200 60" preserveAspectRatio="none">
          <motion.path
            d="M0,30 Q300,10 600,30 T1200,30 L1200,60 L0,60 Z"
            fill="#4059AD"
            opacity="0.1"
            animate={{
              d: [
                'M0,30 Q300,10 600,30 T1200,30 L1200,60 L0,60 Z',
                'M0,30 Q300,50 600,30 T1200,30 L1200,60 L0,60 Z',
                'M0,30 Q300,10 600,30 T1200,30 L1200,60 L0,60 Z',
              ],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        </svg>
      </div>

      {/* Fish */}
      {fishes.map((fish, i) => (
        <Fish key={i} index={fish.index} direction={fish.direction} />
      ))}
    </div>
  );
};
