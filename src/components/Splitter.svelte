<script lang="ts">
  interface Props {
    /** Current size (width or height) - bindable */
    size: number;
    /** Minimum allowed size in pixels */
    min?: number;
    /** Maximum allowed size in pixels */
    max?: number;
    /** 
     * Visual thickness of the splitter bar in pixels.
     * Default: 6 (easy to grab while staying subtle)
     */
    thickness?: number;
    /** Optional title for accessibility */
    title?: string;
  }

  let {
    size = $bindable(),
    min = 0,
    max = Infinity,
    thickness = 6,
    title = 'Drag to resize',
  }: Props = $props();

  let isDragging = $state(false);

  function startDrag(e: MouseEvent) {
    e.preventDefault();
    isDragging = true;

    const onMove = (moveEvent: MouseEvent) => {
      // We only support horizontal (column) splitters for now
      const delta = moveEvent.movementX;
      size = Math.max(min, Math.min(max, size + delta));
    };

    const onUp = () => {
      isDragging = false;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp, { once: true });
  }
</script>

<div
  class="splitter"
  class:dragging={isDragging}
  style:width="{thickness}px"
  onmousedown={startDrag}
  {title}
  role="separator"
  aria-orientation="vertical"
  aria-valuenow={size}
  aria-valuemin={min}
  aria-valuemax={max}
  tabindex="-1"
></div>

<style>
  .splitter {
    cursor: col-resize;
    flex-shrink: 0;
    background-color: transparent;
    transition: background-color 0.15s ease;
    position: relative;
    z-index: 10;
  }

  .splitter:hover {
    background-color: var(--color-sakura, #ff9eb1);
    opacity: 0.3;
  }

  .splitter.dragging {
    background-color: var(--color-sakura, #ff9eb1);
    opacity: 0.5;
  }

  /* Optional subtle grip indicator on hover */
  .splitter::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 2px;
    height: 32px;
    background-color: var(--color-sakura, #ff9eb1);
    border-radius: 1px;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .splitter:hover::after,
  .splitter.dragging::after {
    opacity: 0.6;
  }
</style>
