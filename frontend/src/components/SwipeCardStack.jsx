import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSwipeable } from 'react-swipeable';
import ItemCard from './ItemCard';
import './SwipeCardStack.css';

function SwipeCardStack({ items, onSwipe, currentIndex }) {
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const cardRef = useRef(null);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const isDraggingRef = useRef(false); // Use ref to track dragging state for event listeners

  // Responsive swipe threshold - 25% of screen width, min 80px, max 150px
  const getSwipeThreshold = () => {
    const screenWidth = window.innerWidth;
    const threshold = screenWidth * 0.25;
    return Math.max(80, Math.min(threshold, 150));
  };

  // Get the current item to display
  const currentItem = items[currentIndex];
  const nextItem = items[currentIndex + 1];

  // Handle swipe completion
  const handleSwipeComplete = useCallback((direction) => {
    setSwipeDirection(direction);
    
    // Call the onSwipe callback after animation
    setTimeout(() => {
      onSwipe(direction, items[currentIndex]);
      setSwipeDirection(null);
      setDragOffset({ x: 0, y: 0 });
      setIsDragging(false);
    }, 300);
  }, [onSwipe, items, currentIndex]);

  // Mouse drag start handler
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  // Document-level mouse move handler
  const handleMouseMove = useCallback((e) => {
    if (!isDraggingRef.current) return;
    
    const deltaX = e.clientX - dragStartRef.current.x;
    const deltaY = e.clientY - dragStartRef.current.y;
    
    setDragOffset({ x: deltaX, y: deltaY });
  }, []);

  // Document-level mouse up handler
  const handleMouseUp = useCallback(() => {
    if (!isDraggingRef.current) return;
    
    isDraggingRef.current = false;
    const threshold = getSwipeThreshold();
    
    setDragOffset((currentOffset) => {
      if (Math.abs(currentOffset.x) > threshold) {
        const direction = currentOffset.x > 0 ? 'right' : 'left';
        handleSwipeComplete(direction);
      } else {
        setIsDragging(false);
      }
      return { x: 0, y: 0 };
    });
  }, [handleSwipeComplete]);

  // Add document-level event listeners for mouse drag
  useEffect(() => {
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  // Touch drag handlers (keep these on the element)
  const handleTouchStart = (e) => {
    isDraggingRef.current = true;
    setIsDragging(true);
    dragStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
  };

  const handleTouchMove = (e) => {
    if (!isDraggingRef.current) return;
    if (e.cancelable) e.preventDefault();
    
    const deltaX = e.touches[0].clientX - dragStartRef.current.x;
    const deltaY = e.touches[0].clientY - dragStartRef.current.y;
    
    setDragOffset({ x: deltaX, y: deltaY });
  };

  const handleTouchEnd = () => {
    if (!isDraggingRef.current) return;
    
    isDraggingRef.current = false;
    const threshold = getSwipeThreshold();
    
    setDragOffset((currentOffset) => {
      if (Math.abs(currentOffset.x) > threshold) {
        const direction = currentOffset.x > 0 ? 'right' : 'left';
        handleSwipeComplete(direction);
      } else {
        setIsDragging(false);
      }
      return { x: 0, y: 0 };
    });
  };

  // Swipeable handlers (for touch)
  const handlers = useSwipeable({
    onSwiping: (eventData) => {
      setIsDragging(true);
      setDragOffset({
        x: eventData.deltaX,
        y: eventData.deltaY
      });
    },
    onSwipedLeft: () => {
      const threshold = getSwipeThreshold();
      if (Math.abs(dragOffset.x) > threshold) {
        handleSwipeComplete('left');
      } else {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
    onSwipedRight: () => {
      const threshold = getSwipeThreshold();
      if (Math.abs(dragOffset.x) > threshold) {
        handleSwipeComplete('right');
      } else {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
    onSwiped: () => {
      const threshold = getSwipeThreshold();
      if (Math.abs(dragOffset.x) < threshold) {
        setDragOffset({ x: 0, y: 0 });
        setIsDragging(false);
      }
    },
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
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        role="button"
        tabIndex={0}
        aria-label={`Swipe card for ${currentItem.label}. Drag left to dislike, right to like.`}
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
