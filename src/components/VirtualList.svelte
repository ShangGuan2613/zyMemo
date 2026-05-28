<script lang="ts" generics="T">
  import { onMount } from 'svelte';

  interface Props {
    items: T[];
    itemHeight?: number; // Estimated height for each item (px)
    overscan?: number;
    /** Optional key to force remount when the dataset changes (e.g. different slice) */
    key?: string | number;
    children: (item: T, index: number) => any;
  }

  let {
    items,
    itemHeight = 72, // Reasonable default for chat bubbles
    overscan = 8,
    key,
    children,
  }: Props = $props();

  // Clear measurements when the dataset key changes (e.g. new slice)
  $effect(() => {
    if (key !== undefined) {
      measuredHeights = {};
    }
  });

  let container: HTMLDivElement;
  let scrollTop = $state(0);
  let containerHeight = $state(600);

  // Dynamic height measurement for variable content (e.g. chat bubbles)
  let measuredHeights = $state<Record<number, number>>({});

  function getItemHeight(index: number): number {
    return measuredHeights[index] ?? itemHeight;
  }

  // Calculate visible range using estimated height (good enough for range)
  let startIndex = $derived(Math.max(0, Math.floor(scrollTop / itemHeight) - overscan));
  let endIndex = $derived(
    Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    )
  );

  let visibleItems = $derived(items.slice(startIndex, endIndex + 1));

  // Use measured heights for accurate spacers
  let topSpacerHeight = $derived.by(() => {
    let h = 0;
    for (let i = 0; i < startIndex; i++) {
      h += getItemHeight(i);
    }
    return h;
  });

  let bottomSpacerHeight = $derived.by(() => {
    let h = 0;
    for (let i = endIndex + 1; i < items.length; i++) {
      h += getItemHeight(i);
    }
    return h;
  });

  function onScroll() {
    if (container) {
      scrollTop = container.scrollTop;
    }
  }

  onMount(() => {
    if (container) {
      const resizeObserver = new ResizeObserver(() => {
        containerHeight = container.clientHeight;
      });
      resizeObserver.observe(container);

      return () => resizeObserver.disconnect();
    }
  });

  // Action to measure actual rendered height of each item
  function measureHeight(el: HTMLElement, index: number) {
    const ro = new ResizeObserver(() => {
      const height = el.getBoundingClientRect().height;
      if (measuredHeights[index] !== height) {
        measuredHeights[index] = height;
      }
    });
    ro.observe(el);

    return {
      destroy() {
        ro.disconnect();
      }
    };
  }
</script>

<div
  bind:this={container}
  onscroll={onScroll}
  class="h-full overflow-y-auto"
  style="contain: strict;"
>
  <div style="height: {topSpacerHeight}px;"></div>

  {#each visibleItems as item, i (i)}
    {@const actualIndex = startIndex + i}
    <div 
      style="min-height: {itemHeight}px;"
      use:measureHeight={actualIndex}
    >
      {@render children(item, actualIndex)}
    </div>
  {/each}

  <div style="height: {bottomSpacerHeight}px;"></div>
</div>
