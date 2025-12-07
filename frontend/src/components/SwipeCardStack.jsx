import React, { useState, useRef } from 'react';
import { useSwipeable } from 'react-swipeable';
import ItemCard from './ItemCard';
import './SwipeCardStack.css';

function SwipeCardStack({ items, onSwipe, currentIndex }) {
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const cardRef = useRef(null);

  // Get the current item to display
  const currentItem = items[currentIndex];
  const nextItem = items[currentIndex + 1];

  // Handle swipe completion
  const handleSwipeComplete = (direction) => {
    setSwipeDirection(direction);
    
    // Call the onSwipe callback after animation
    setTimeout(() => {
      onSwipe(direction, currentItem);
      setSwipeDirection(null);
      setDragOffset({ x: 0, y: 0 });
      setIsDragging(false);
    }, 300);
  };

  // Swipeable handlers
  const handlers = useSwipeable({
    onSwiping: (eventData) => {
      setIsDragging(true);
      setDragOffset({
        x: eventData.deltaX,
        y: eventData.deltaY
      });
    },
    onSwipedLeft: () => {
      if (Math.abs(dragOffset.x) > 100) {
        handleSwipeComplete('left');
      } else {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
    onSwipedRight: () => {
      if (Math.abs(dragOffset.x) > 100) {
        handleSwipeComplete('right');
      } else {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
    onSwiped: () => {
      if (Math.abs(dragOffset.x) < 100) {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
    trackMouse: true,
    trackTouch: true,
    preventScrollOnSwipe: true,
  });

  // Calculate rotation and opacity based on drag
  const getCardStyle = () => {
    if (swipeDirection) {
      // Animation when swiping away
      const direction = swipeDirection === 'right' ? 1 : -1;
      return {
        transform: `translateX(${direction * 500}px) rotate(${direction * 30}deg)`,
        opacity: 0,
        transition: 'all 0.3s ease-out',
      };
    }

    if (isDragging) {
      // Live dragging
      const rotation = dragOffset.x / 20;
      return {
        transform: `translateX(${dragOffset.x}px) translateY(${dragOffset.y}px) rotate(${rotation}deg)`,
        transition: 'none',
      };
    }

    // Default position
    return {
      transform: 'translateX(0) translateY(0) rotate(0deg)',
      transition: 'all 0.3s ease-out',
    };
  };

  // Calculate overlay opacity
  const getOverlayOpacity = () => {
    if (swipeDirection) {
      return 1;
    }
    return Math.min(Math.abs(dragOffset.x) / 150, 1);
  };

  if (!currentItem) {
    return (
      <div className="swipe-card-stack">
        <div className="no-items-message">
          <h2>No more items to vote on!</h2>
          <p>Check back later or view the favourites.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="swipe-card-stack">
      {/* Next card (background) */}
      {nextItem && (
        <div className="card-wrapper card-background">
          <ItemCard item={nextItem} />
        </div>
      )}

      {/* Current card (foreground) */}
      <div
        {...handlers}
        ref={cardRef}
        className="card-wrapper card-foreground"
        style={getCardStyle()}
      >
        <ItemCard item={currentItem} />
        
        {/* Swipe overlays */}
        <div
          className="swipe-overlay swipe-overlay-like"
          style={{
            opacity: dragOffset.x > 0 ? getOverlayOpacity() : 0,
          }}
        >
          <span className="overlay-text">LIKE</span>
        </div>
        <div
          className="swipe-overlay swipe-overlay-dislike"
          style={{
            opacity: dragOffset.x < 0 ? getOverlayOpacity() : 0,
          }}
        >
          <span className="overlay-text">NOPE</span>
        </div>
      </div>
    </div>
  );
}

export default SwipeCardStack;
