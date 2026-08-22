import React, { useEffect, useRef, useState } from 'react';

/* ========================================================================== */
/* PRICE TICKER — Flashes green/red on price change                           */
/* ========================================================================== */

interface PriceTickerProps {
  price: number;
  previousPrice?: number;
  decimals?: number;
  className?: string;
}

export const PriceTicker: React.FC<PriceTickerProps> = ({
  price,
  previousPrice,
  decimals = 2,
  className = '',
}) => {
  const [flash, setFlash] = useState<'green' | 'red' | null>(null);
  const prevRef = useRef(previousPrice ?? price);

  useEffect(() => {
    if (price > prevRef.current) {
      setFlash('green');
    } else if (price < prevRef.current) {
      setFlash('red');
    }
    prevRef.current = price;

    const timer = setTimeout(() => setFlash(null), 350);
    return () => clearTimeout(timer);
  }, [price]);

  return (
    <span
      data-mono
      className={`
        inline-block px-1 rounded-[2px] transition-colors duration-150
        ${flash === 'green' ? 'flash-green text-profit' : ''}
        ${flash === 'red' ? 'flash-red text-loss' : ''}
        ${!flash ? 'text-text-primary' : ''}
        ${className}
      `}
    >
      {price.toFixed(decimals)}
    </span>
  );
};
