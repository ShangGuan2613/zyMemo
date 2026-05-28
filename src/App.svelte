<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { readFile } from '@tauri-apps/plugin-fs';
  import VirtualList from './components/VirtualList.svelte';
  import Splitter from './components/Splitter.svelte';
  // Note: We no longer import runtime mock data here.
  // All data should come through Tauri commands for architecture cleanliness.
  // The rich mock data now lives in Rust's MockRepository.

  // Slices now come from Rust layer (architecture boundary)
  let allSlices = $state<any[]>([]);

  // Load slices from backend on startup
  $effect(() => {
    invoke('get_slices')
      .then((slices: any) => {
        allSlices = slices;

        if (!currentSliceId && slices.length > 0) {
          // 真实数据场景：默认选中最近一个月的第一天，并展开该月
          const latest = slices[0]; // 假设后端按时间倒序返回
          currentSliceId = latest.id;

          // 尝试展开它所属的月份
          const month = latest.month || (latest.startDate ? latest.startDate.substring(0,7) : null);
          if (month) {
            expandedMonths.add(month);
            expandedMonths = new Set(expandedMonths);
          }
        }
      })
      .catch(() => {
        // Fallback during early development
        allSlices = [
          { id: 'slice_0320', title: '3月20-21日 三亚旅行', messageCount: 180, startDate: '2025-03-20' },
          { id: 'slice_0328', title: '3月28日 纪念日', messageCount: 156, startDate: '2025-03-28' },
        ];
        if (!currentSliceId) currentSliceId = 'slice_0320';
      });
  });
  // Svelte 5 runes for clean state (low maintenance)
  let currentTab = $state<'text' | 'media'>('text');
  let selectedId = $state<string | null>(null);
  let currentSliceId = $state<string | null>('slice_0320'); // 默认选中数据量大的三亚旅行 slice，便于测试虚拟滚动

  // === Realistic UI State for Splitters (will persist to settings later) ===
  let leftWidth = $state(260);
  let rightWidth = $state(280);

  const MIN_LEFT = 200;
  const MAX_LEFT = 380;
  const MIN_RIGHT = 220;
  const MAX_RIGHT = 420;

  // 当前 slice 的消息（从 Rust 层获取）
  let currentMessages = $state<any[]>([]);

  $effect(() => {
    if (currentSliceId) {
      invoke('get_messages_by_slice', { sliceId: currentSliceId })
        .then((msgs: any) => (currentMessages = msgs))
        .catch((err) => {
          console.error('Failed to load messages from backend:', err);
          currentMessages = []; // Strict: no silent fallback to old TS mocks
        });
    }
  });

  // Splitter drag logic is now fully encapsulated inside <Splitter> component

  // Old inline mocks removed - using rich data from src/lib/mockData.ts instead
  // (kept for reference during migration)

  let selectedItem: any = $derived.by(() => {
    if (!selectedId) return null;
    if (currentTab === 'text') {
      return currentMessages.find(m => m.id === selectedId);
    } else {
      return currentMedia.find(m => m.id === selectedId);
    }
  });

  // 当前 slice 的批注（从 Rust 层获取）
  let currentAnnotations = $state<any[]>([]);
  let newlySavedAnnotationId = $state<string | null>(null);

  // 根据当前模式和选中项，决定右侧显示哪些批注
  let displayedAnnotations = $derived.by(() => {
    if (selectedId) {
      if (currentTab === 'media') {
        // 媒体模式下选中具体照片 → 只显示这条照片的批注
        return currentAnnotations.filter(
          a => a.targetType === 'media' && a.targetId === selectedId
        );
      } else {
        // 文字模式下选中具体消息 → 只显示这条消息的批注
        return currentAnnotations.filter(
          a => a.targetType === 'message' && a.targetId === selectedId
        );
      }
    }
    // 没有选中具体项时，显示当前上下文的所有批注
    return currentAnnotations;
  });

  // 批注表单状态（支持新增和编辑）
  let annotationContent = $state('');
  let selectedTags = $state<string[]>([]);
  let editingAnnotationId = $state<string | null>(null);

  // 温柔删除 + 撤销状态（极简实现，不引入新组件）
  let pendingDeleteId = $state<string | null>(null);
  let undoAnnotation = $state<any | null>(null);
  let undoTimer: ReturnType<typeof setTimeout> | null = null;

  $effect(() => {
    if (currentSliceId) {
      invoke('get_annotations_for_slice', { sliceId: currentSliceId })
        .then((anns: any) => {
          currentAnnotations = anns;
        })
        .catch((err) => {
          console.error('Failed to load annotations from backend:', err);
          currentAnnotations = [];
        });
    }
  });

  // 清除新批注高亮
  $effect(() => {
    if (newlySavedAnnotationId) {
      const timer = setTimeout(() => {
        newlySavedAnnotationId = null;
      }, 2200);
      return () => clearTimeout(timer);
    }
  });

  // 当前 slice 的媒体（从 Rust 层获取）
  let currentMedia = $state<any[]>([]);

  // 当前媒体类型（目前只支持图片）
  let currentMediaCategory = $state<'image' | null>(null);

  // 图片数量
  let mediaCounts = $state({
    image: 0
  });

  // Simple loading flag for the photo grid (important for large real datasets ~4000+ images)
  let isLoadingMediaGrid = $state(false);

  // Simple cache for blob URLs to avoid re-reading files constantly
  const mediaBlobUrls = new Map<string, string>();

  async function getMediaPreviewUrl(media: any): Promise<string> {
    if (mediaBlobUrls.has(media.id)) {
      return mediaBlobUrls.get(media.id)!;
    }

    try {
      const filePath = media.url;
      const data = await readFile(filePath);
      const blob = new Blob([data], { type: 'image/jpeg' });
      const url = URL.createObjectURL(blob);
      mediaBlobUrls.set(media.id, url);
      return url;
    } catch (err) {
      console.error("Failed to load image file via fs plugin:", err);
      throw err;
    }
  }

  // 清理并美化图片标题
  function formatMediaTitle(title: string | null | undefined): string {
    if (!title) return '未命名照片';
    // 微信典型的 hash 文件名 → 显示为“照片”
    if (/^\d+_[a-f0-9]+\.(jpg|jpeg|png|gif|webp)$/i.test(title)) {
      return '照片';
    }
    // 去掉扩展名，让标题更干净
    return title.replace(/\.[^/.]+$/, '');
  }

  // 格式化日期时间（从 created_at）
  function formatMediaDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      return d.toLocaleString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  // 人类可读的文件大小
  function formatFileSize(bytes: number | null | undefined): string {
    if (!bytes || bytes === 0) return '';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  }

  // 格式化图片尺寸
  function formatDimensions(width: number | null | undefined, height: number | null | undefined): string {
    if (!width || !height) return '';
    return `${width}×${height}`;
  }

  // 情绪标签 → 可爱徽章（颜色 + emoji 映射，符合整体治愈风格）
  function getEmotionBadge(emotion: string | null | undefined): { emoji: string; label: string; bg: string; text: string } {
    const e = (emotion || '日常').trim();
    const map: Record<string, { emoji: string; label: string; bg: string; text: string }> = {
      '开心': { emoji: '😊', label: '开心', bg: '#d1fae5', text: '#166534' },   // mint green
      '甜蜜': { emoji: '💕', label: '甜蜜', bg: '#fce7f3', text: '#9f1239' },   // sakura pink
      '感动': { emoji: '🥹', label: '感动', bg: '#e0e7ff', text: '#3730a3' },   // soft indigo
      '想念': { emoji: '🌙', label: '想念', bg: '#ede9fe', text: '#5b21b6' },   // lavender
      '日常': { emoji: '🌿', label: '日常', bg: '#fef3c7', text: '#854d0e' },   // warm sand
      '争执': { emoji: '🌧️', label: '争执', bg: '#e5e7eb', text: '#374151' },   // calm gray
    };
    return map[e] || { emoji: '💬', label: e, bg: '#f3e8d8', text: '#5c4636' };
  }

  // 清理照片 blob URLs（针对真实大图库的内存适配）
  function cleanupPhotoBlobs() {
    for (const url of mediaBlobUrls.values()) {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {
        // 忽略 revoke 错误
      }
    }
    mediaBlobUrls.clear();
  }

  $effect(() => {
    // 进入媒体 tab 时加载图片数量
    if (currentTab === 'media') {
      invoke<any[]>('get_media_by_type', { mediaType: 'image' })
        .then((list) => {
          mediaCounts.image = list.length;
          mediaCounts = { ...mediaCounts };
        })
        .catch((e) => {
          console.error('Failed to count images:', e);
        });
    }

    // 媒体库只加载图片
    if (currentMediaCategory === 'image') {
      isLoadingMediaGrid = true;
      invoke('get_media_by_type', { mediaType: 'image' })
        .then((media: any) => {
          currentMedia = media;
        })
        .catch((err) => {
          console.error('Failed to load images:', err);
          currentMedia = [];
        })
        .finally(() => {
          isLoadingMediaGrid = false;
        });
      return;
    }

    // 如果从图片模式切换走，清理已加载的照片 blob
    if (currentMediaCategory !== 'image' && mediaBlobUrls.size > 0) {
      cleanupPhotoBlobs();
    }

    // 聊天记录模式下也加载该 slice 的图片（用于批注上下文）
    if (currentSliceId) {
      invoke('get_media_by_slice', { sliceId: currentSliceId })
        .then((media: any) => {
          currentMedia = media;
        })
        .catch((err) => {
          console.error('Failed to load media from backend:', err);
          currentMedia = [];
        });
    }
  });

  function selectItem(id: string) {
    clearDeleteState();
    selectedId = id;
  }

  function switchTab(tab: 'text' | 'media') {
    pendingDeleteId = null;
    if (undoAnnotation) cancelUndo();

    currentTab = tab;
    selectedId = null;

    if (tab === 'media') {
      currentMediaCategory = 'image';
    } else {
      // 离开媒体库时清理照片 blob，避免长期占用内存（真实数据适配）
      if (currentMediaCategory === 'image') {
        cleanupPhotoBlobs();
      }
      currentMediaCategory = null;
      currentMedia = [];
      isLoadingMediaGrid = false;
    }
  }

  async function saveAnnotation() {
    if (!selectedItem || !selectedId || !annotationContent.trim()) return;

    const now = new Date().toISOString();
    const isEditing = !!editingAnnotationId;

    const annToSave = {
      id: isEditing ? editingAnnotationId : 'a' + Date.now(),
      targetType: currentTab === 'text' ? 'message' : 'media',
      targetId: selectedId,
      content: annotationContent.trim(),
      tags: [...selectedTags],
      createdAt: isEditing ? undefined : now,
      updatedAt: now,
    };

    await invoke('save_annotation', { annotation: annToSave });

    if (currentSliceId) {
      // 正常按 slice 刷新
      const anns = await invoke('get_annotations_for_slice', { sliceId: currentSliceId });
      currentAnnotations = anns as any[];
    } else {
      // 全局照片模式（currentSliceId 为 null）：本地追加这条新批注
      // 这样单张照片的批注不会污染整个页面
      currentAnnotations = [...currentAnnotations, annToSave];
    }

    newlySavedAnnotationId = annToSave.id;

    // 保存新批注时清空任何待撤销状态
    if (undoAnnotation) cancelUndo();

    annotationContent = '';
    selectedTags = [];
    editingAnnotationId = null;
  }

  // === 温柔删除流程（替代原生 confirm，带 5 秒撤销） ===
  function requestDelete(id: string) {
    // 如果正在撤销另一条，先取消
    if (undoAnnotation) cancelUndo();
    pendingDeleteId = id;
  }

  async function confirmDelete() {
    if (!pendingDeleteId) return;
    const idToDelete = pendingDeleteId;

    // 先从当前列表里找到完整对象，用于撤销
    const toUndo = currentAnnotations.find(a => a.id === idToDelete) || displayedAnnotations.find(a => a.id === idToDelete);

    await invoke('delete_annotation', { id: idToDelete });

    // 刷新列表
    const anns = await invoke('get_annotations_for_slice', { sliceId: currentSliceId });
    currentAnnotations = anns as any[];

    // 如果正在编辑的就是被删除的这条，清空表单
    if (editingAnnotationId === idToDelete) {
      cancelEdit();
    }

    // 进入撤销状态（5 秒）
    pendingDeleteId = null;
    undoAnnotation = toUndo || { id: idToDelete };

    // 自动清除撤销提示
    if (undoTimer) clearTimeout(undoTimer);
    undoTimer = setTimeout(() => {
      undoAnnotation = null;
      undoTimer = null;
    }, 5000);
  }

  function cancelPendingDelete() {
    pendingDeleteId = null;
  }

  async function performUndo() {
    if (!undoAnnotation) return;

    const ann = { ...undoAnnotation };
    // 重新保存（save_annotation 会 INSERT OR REPLACE）
    await invoke('save_annotation', { annotation: ann });

    const refreshed = await invoke('get_annotations_for_slice', { sliceId: currentSliceId });
    currentAnnotations = refreshed as any[];

    // 高亮刚刚撤销回来的那条
    newlySavedAnnotationId = ann.id;

    cancelUndo();
  }

  function cancelUndo() {
    if (undoTimer) {
      clearTimeout(undoTimer);
      undoTimer = null;
    }
    undoAnnotation = null;
  }


  function startEditAnnotation(ann: any) {
    // 编辑时自动取消任何待删除/撤销状态
    if (pendingDeleteId || undoAnnotation) cancelUndo();
    pendingDeleteId = null;

    annotationContent = ann.content || '';
    selectedTags = [...(ann.tags || [])];
    editingAnnotationId = ann.id;
  }

  function cancelEdit() {
    annotationContent = '';
    selectedTags = [];
    editingAnnotationId = null;
  }

  function toggleTag(tag: string) {
    if (selectedTags.includes(tag)) {
      selectedTags = selectedTags.filter(t => t !== tag);
    } else {
      selectedTags = [...selectedTags, tag];
    }
  }

  function getAnnotationPlaceholder(): string {
    if (!selectedItem) return '写下此刻的心情或想记住的细节…';

    if (currentTab === 'text') {
      return '给这条消息写点小纸条…';
    } else {
      return '给这张照片写点回忆…';
    }
  }

  // 极简目标类型徽章（用于混合列表，让用户一眼看懂这条小纸条写给谁）
  function getAnnotationTargetBadge(ann: any) {
    const type = ann.targetType || 'slice';
    const targetId = ann.targetId || '';

    if (type === 'media') {
      const mediaItem = currentMedia.find(m => m.id === targetId);
      let label = mediaItem ? mediaItem.title : '照片';
      if (label.length > 8) label = label.slice(0, 7) + '…';
      return { icon: '📷', label, kind: 'media' as const };
    }
    if (type === 'message') {
      return { icon: '💬', label: '消息', kind: 'message' as const };
    }
    return { icon: '📅', label: '事件', kind: 'slice' as const };
  }

  // Helper for making custom clickable elements keyboard accessible (Enter / Space)
  function handleActivation(event: KeyboardEvent, handler: () => void) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handler();
    }
  }

  // 切换上下文时统一清空删除/撤销状态（保持心智模型干净）
  function clearDeleteState() {
    pendingDeleteId = null;
    if (undoAnnotation) cancelUndo();
  }

  // === 新增：月份分组 + 展开状态（用于层级目录）===
  let expandedMonths = $state<Set<string>>(new Set());

  // 将 daily slices 按月份分组
  let groupedSlicesByMonth = $derived.by(() => {
    if (currentTab !== 'text' || allSlices.length === 0) return {} as Record<string, any[]>;

    const groups: Record<string, any[]> = {};
    for (const slice of allSlices) {
      // 优先使用 slice.month（导入时保留的），否则从 startDate 取
      const month = slice.month || (slice.startDate ? slice.startDate.substring(0, 7) : 'unknown');
      if (!groups[month]) groups[month] = [];
      groups[month].push(slice);
    }

    // 每个月份内的日期按时间排序
    for (const m in groups) {
      groups[m].sort((a: any, b: any) => (a.startDate || '').localeCompare(b.startDate || ''));
    }

    return groups;
  });

  const sortedMonths = $derived(Object.keys(groupedSlicesByMonth).sort().reverse()); // 最近的月份在前

  function toggleMonth(month: string) {
    if (expandedMonths.has(month)) {
      expandedMonths.delete(month);
    } else {
      expandedMonths.add(month);
    }
    // 强制 Svelte 响应
    expandedMonths = new Set(expandedMonths);
  }

  function selectFirstDayOfMonth(month: string) {
    const days = groupedSlicesByMonth[month];
    if (!days || days.length === 0) return;

    const firstDay = days[0];
    clearDeleteState();
    currentSliceId = firstDay.id;
    selectedId = null;
    if (currentTab !== 'text') currentTab = 'text';

    // 自动展开这个月份
    if (!expandedMonths.has(month)) {
      expandedMonths.add(month);
      expandedMonths = new Set(expandedMonths);
    }
  }

  function selectDay(daySlice: any) {
    clearDeleteState();
    currentSliceId = daySlice.id;
    selectedId = null;
    if (currentTab !== 'text') currentTab = 'text';
  }

  // Format full ISO time to HH:mm for bubble display
  function formatTime(isoTime: string): string {
    if (!isoTime) return '';
    try {
      const d = new Date(isoTime);
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch {
      return isoTime;
    }
  }

  // 把 "2025-04" 格式化成 "2025年4月"
  function formatMonthLabel(month: string): string {
    if (!month || month === 'unknown') return '未知月份';
    const [year, mon] = month.split('-');
    return `${year}年${parseInt(mon)}月`;
  }
</script>

<div class="app-root bg-cream text-cocoa h-screen flex flex-col">
  <!-- Top bar -->
  <div class="h-12 bg-almond border-b border-beige/60 flex items-center px-6 gap-4 text-sm font-medium shrink-0">
    <div class="text-sakura text-[15px]">🌸 zyMemo</div>
    <div class="text-cocoa flex-1">在楼下</div>
  </div>

  <div class="flex-1 flex overflow-hidden">
    <!-- LEFT: Directory -->
    <div 
      class="bg-almond border-r border-beige/60 p-4 overflow-y-auto shrink-0" 
      style="width: {leftWidth}px; min-width: {MIN_LEFT}px; max-width: {MAX_LEFT}px;"
    >
      <div class="flex gap-2 mb-4">
        <button 
          class="flex-1 py-2.5 rounded-full text-sm transition-all {currentTab === 'text' ? 'bg-gradient-to-r from-sakura to-mint text-white shadow-healing' : 'bg-beige text-cocoa'}"
          onclick={() => switchTab('text')}
        >
          💬 文字聊天
        </button>
        <button 
          class="flex-1 py-2.5 rounded-full text-sm transition-all {currentTab === 'media' ? 'bg-gradient-to-r from-sakura to-mint text-white shadow-healing' : 'bg-beige text-cocoa'}"
          onclick={() => switchTab('media')}
        >
          🖼️ 图片库
        </button>
      </div>

      {#if currentTab === 'text'}
        <div class="text-[11px] uppercase tracking-[0.5px] text-taupe mb-2 mt-3">聊天记录</div>
        
        {#each sortedMonths as month}
          {@const isExpanded = expandedMonths.has(month)}
          {@const days = groupedSlicesByMonth[month] || []}
          {@const firstDay = days[0]}
          
          <!-- 月份头 -->
          <div 
            class="month-header flex items-center justify-between px-3 py-2 rounded-xl mb-1 cursor-pointer text-sm font-medium
                   {isExpanded ? 'bg-[#f0e6d9]' : 'hover:bg-[#f8f1eb]'}"
            onclick={() => selectFirstDayOfMonth(month)}
            role="button"
            tabindex="0"
          >
            <div class="flex items-center gap-2">
              <span class="text-base">{isExpanded ? '▼' : '▶'}</span>
              <span>{formatMonthLabel(month)}</span>
            </div>
            <span class="text-xs text-taupe">{days.length}天</span>
          </div>
          
          <!-- 该月下的日期列表 -->
          {#if isExpanded}
            {#each days as daySlice}
              <div 
                class="day-item ml-6 px-3 py-1.5 rounded-xl mb-0.5 text-sm cursor-pointer flex justify-between items-center
                       {currentSliceId === daySlice.id ? 'bg-[#ffe4e1] border-l-3 border-[#ff9eb1]' : 'hover:bg-[#f8f1eb]'}"
                role="button"
                tabindex="0"
                onclick={() => selectDay(daySlice)}
                onkeydown={(e) => handleActivation(e, () => selectDay(daySlice))}
              >
                <span>{daySlice.title}</span>
                <span class="text-xs text-taupe">{daySlice.messageCount} 条</span>
              </div>
            {/each}
          {/if}
        {/each}
        
      {:else}
        <div class="text-[11px] uppercase tracking-[0.5px] text-taupe mb-2 mt-3">图片</div>
        
        <!-- 图片分类（当前只做图片） -->
        <div 
          class="px-3 py-2.5 bg-[#f8f1eb] rounded-2xl cursor-pointer text-sm flex justify-between items-center transition-all
                 {currentTab === 'media' ? 'bg-[#ffe4e1] border-l-3 border-[#ff9eb1]' : 'hover:bg-[#fffaf0]'}"
          role="button"
          tabindex="0"
          onclick={() => {
            currentMediaCategory = 'image';
            currentSliceId = null;
            selectedId = null;
            currentAnnotations = [];   // 清空之前 slice 的批注，避免泄露到全局照片模式
            if (currentTab !== 'media') currentTab = 'media';
          }}
        >
          <span>🖼️ 图片</span>
          <span class="text-xs text-taupe">({mediaCounts.image})</span>
        </div>
      {/if}
    </div>

    <!-- LEFT SPLITTER -->
    <Splitter 
      bind:size={leftWidth} 
      min={MIN_LEFT} 
      max={MAX_LEFT}
      title="拖拽调整左侧宽度"
    />

    <!-- MIDDLE: Content Viewer (flexible, fills remaining space) -->
    <div class="middle-panel flex-1 flex flex-col min-w-0 overflow-hidden bg-white">
      <div class="content-header shrink-0">
        {#if currentTab === 'text'}
          💬 聊天记录
          <span class="hint text-xs">({currentMessages.length} 条)</span>
        {:else}
          🖼️ 图片库
          <span class="hint text-xs">({currentMedia.length} 张)</span>
        {/if}
      </div>

      {#if currentTab === 'text'}
        <!-- Virtual Scrolling Chat (realistic for large exports) -->
        <!-- The wrapper provides the height constraint; VirtualList handles its own scrolling -->
        <div class="flex-1 min-h-0">
          <VirtualList items={currentMessages} itemHeight={68} key={currentSliceId ?? 'default'}>
            {#snippet children(msg: any, _index: number)}
              <div 
                class="bubble mx-auto max-w-[620px]"
                class:from-me={msg.fromMe}
                role="button"
                tabindex="0"
                onclick={() => selectItem(msg.id)}
                onkeydown={(e) => handleActivation(e, () => selectItem(msg.id))}
                class:selected={selectedId === msg.id}
              >
                <div class="bubble-content">
                  {#if msg.type === 'text'}
                    {msg.content}
                  {:else if msg.type === 'sticker'}
                    [表情] {msg.content}
                  {:else if msg.type === 'image'}
                    📷 [图片] {msg.content}
                  {:else if msg.type === 'voice'}
                    🎤 [语音] {msg.content}
                  {:else}
                    {msg.content}
                  {/if}
                </div>
                <div class="bubble-time">{formatTime(msg.time)}</div>
              </div>
            {/snippet}
          </VirtualList>
        </div>
      {:else}
        <!-- Media Grid - 照片相册（当前专注适配与性能） -->
        <div class="flex-1 min-h-0 overflow-y-auto p-5" style="background: #f5f0e9;">
          {#if isLoadingMediaGrid}
            <div class="empty-state">
              <div class="empty-icon">📷</div>
              <p>正在加载照片列表...</p>
            </div>
          {:else if currentMedia.length === 0}
            <div class="empty-state">
              <div class="empty-icon">📭</div>
              <p>这个分类目前还没有媒体文件</p>
            </div>
          {:else}
            <div class="media-grid">
              {#each currentMedia as media}
                <div 
                  class="media-card"
                  class:selected={selectedId === media.id}
                  role="button"
                  tabindex="0"
                  onclick={() => selectItem(media.id)}
                  onkeydown={(e) => handleActivation(e, () => selectItem(media.id))}
                >
                  <!-- 照片主体 -->
                  {#await getMediaPreviewUrl(media)}
                    <div class="media-placeholder loading" style="aspect-ratio:1; width:100%;">· · ·</div>
                  {:then url}
                    <img 
                      src={url} 
                      alt={media.title}
                      class="photo"
                    />
                  {:catch}
                    <div class="media-placeholder" style="aspect-ratio:1; width:100%;">—</div>
                  {/await}

                  <div class="info">
                    <div class="meta">
                      {#if media.width && media.height}
                        <span class="dim">{media.width}×{media.height}</span>
                      {/if}
                      {#if media.size_bytes}
                        <span class="size">{formatFileSize(media.size_bytes)}</span>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- RIGHT SPLITTER -->
    <Splitter 
      bind:size={rightWidth} 
      min={MIN_RIGHT} 
      max={MAX_RIGHT}
      title="拖拽调整右侧批注栏宽度"
    />

    <!-- RIGHT: Annotation Panel -->
    <div 
      class="bg-almond border-l border-beige/60 p-4 overflow-y-auto shrink-0"
      style="width: {rightWidth}px; min-width: {MIN_RIGHT}px; max-width: {MAX_RIGHT}px;"
    >
      <div class="anno-header">
        📝 我的小纸条
        {#if selectedItem}
          <div class="target-hint">
            {#if currentTab === 'text'}
              针对这条消息
            {:else if selectedId}
              这张照片的小纸条
            {:else}
              当前上下文的批注
            {/if}
          </div>
        {/if}
      </div>

      <!-- 让批注内容居中放置（体验优化），面板本身仍可拖宽 -->
      <div class="anno-centered">

      {#if selectedItem}
        <div class="anno-list">
          {#each displayedAnnotations as ann}
            <div class="anno-card" class:newly-saved={ann.id === newlySavedAnnotationId}>
              <div class="anno-card-header">
                {#if true}
                  {@const badge = getAnnotationTargetBadge(ann)}
                  <span class="target-badge" class:media={badge.kind === 'media'} class:message={badge.kind === 'message'} class:slice={badge.kind === 'slice'}>
                    {badge.icon} {badge.label}
                  </span>
                {/if}
                <div class="tags">
                  {#each ann.tags as tag}
                    <span class="tag">{tag}</span>
                  {/each}
                </div>
                <div class="anno-actions">
                  <button class="edit-btn" onclick={() => startEditAnnotation(ann)}>编辑</button>
                  <button class="delete-btn" onclick={() => requestDelete(ann.id)}>删除</button>
                </div>
              </div>
              <div class="anno-content">{ann.content}</div>
            </div>
          {/each}
        </div>

        <!-- 温柔删除确认 + 撤销提示（极简、温暖、无新组件） -->
        {#if pendingDeleteId}
          <div class="delete-confirm-bar">
            <span>确定要删除这条小纸条吗？</span>
            <div class="confirm-actions">
              <button class="confirm-delete-btn" onclick={confirmDelete}>删除</button>
              <button class="cancel-btn" onclick={cancelPendingDelete}>取消</button>
            </div>
          </div>
        {:else if undoAnnotation}
          <div class="undo-toast">
            <span>已删除小纸条</span>
            <button class="undo-btn" onclick={performUndo}>撤销</button>
            <button class="undo-close" onclick={cancelUndo}>×</button>
          </div>
        {/if}

        <div class="add-form">
          {#if currentTab === 'media' && selectedId}
            <div class="form-context-hint">正在为这张照片写回忆</div>
          {/if}

          <textarea 
            placeholder={getAnnotationPlaceholder()}
            rows="3"
            bind:value={annotationContent}
          ></textarea>
          
          <div class="tag-row">
            {#each ['感动','甜蜜','想念','纪念','日常','有趣','争吵','故事'] as tag}
              <button 
                class="tag-btn"
                class:selected={selectedTags.includes(tag)}
                onclick={() => toggleTag(tag)}
              >
                {tag}
              </button>
            {/each}
          </div>

          <div class="form-actions">
            <button class="save-btn" onclick={saveAnnotation} disabled={!annotationContent.trim()}>
              {editingAnnotationId ? '💾 更新批注' : '💾 保存批注'}
            </button>
            {#if editingAnnotationId}
              <button class="cancel-btn" onclick={cancelEdit}>
                取消
              </button>
            {/if}
          </div>
        </div>
      {:else}
        <div class="empty-state centered-in-panel">
          <div class="empty-icon">🐻</div>
          <p>在中间区域点击一条消息或照片<br>就可以在这里写小纸条啦 ❤️</p>
        </div>
      {/if}
      </div>   <!-- / .anno-centered -->
    </div>
  </div>
</div>

<style>
  /* 组件特定样式（保留气泡、卡片等难以用纯工具类1:1复刻的可爱细节；简单规则已逐步迁移到 Tailwind） */

  /* 左侧列表项 - 部分已迁移到 Tailwind，保留必要状态样式 */
  .slice-item {
    padding: 10px 12px;
    border-radius: 16px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .slice-item:hover { background: #f8f1eb; }
  .slice-item.selected { background: #ffe4e1; border-left: 3px solid #ff9eb1; }
  .slice-title { font-weight: 500; color: #5c4636; }
  .slice-meta { font-size: 11px; color: #8c7563; margin-top: 2px; }

  /* 月份层级目录样式 */
  .month-header {
    font-weight: 600;
    color: #5c4636;
    transition: background-color 0.1s;
  }
  .month-header:hover {
    background: #f8f1eb;
  }

  .day-item {
    font-size: 13px;
    color: #5c4636;
    transition: all 0.1s;
  }



  .content-header {
    font-size: 15px;
    font-weight: 600;
    color: #5c4636;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  /* Middle panel must grow to fill all remaining horizontal space between left and right panes */
  .middle-panel {
    flex: 1 1 auto;
    min-width: 0;           /* prevents flex child from overflowing when content is wide */
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: #fffaf0;    /* almond-like content bg for warmth */
  }

  .chat-flow {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 620px;   /* keep nice readable width for chat bubbles */
    margin: 0 auto;     /* center the chat column */
  }
  .bubble {
    max-width: 78%;
    padding: 12px 18px;
    border-radius: 22px;
    font-size: 14px;
    line-height: 1.45;
    cursor: pointer;
    transition: transform 0.1s, box-shadow 0.1s;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .bubble.from-me {
    align-self: flex-end;
    background: #ff9eb1;
    color: white;
    border-bottom-right-radius: 6px;
  }
  .bubble:not(.from-me) {
    background: #a8e6cf;
    color: #3a4d3f;
    border-bottom-left-radius: 6px;
  }
  .bubble.selected { outline: 2px solid #5c4636; outline-offset: 2px; }
  .bubble-content { white-space: pre-wrap; }
  .bubble-time {
    font-size: 10px;
    opacity: 0.65;
    margin-top: 4px;
    text-align: right;
  }

  .media-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(152px, 1fr));
    gap: 14px;
    align-items: start;
  }
  .media-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    position: relative;
    background: white;
    border: 1px solid #e8dcc8;
  }
  .media-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.09);
    border-color: #d4c9b8;
  }
  .media-card.selected {
    outline: 2px solid #ff9eb1;
    outline-offset: 2px;
    border-color: #ff9eb1;
    box-shadow: 0 4px 14px rgba(255, 158, 177, 0.15);
  }

  .media-card .photo {
    width: 100%;
    aspect-ratio: 1;
    background: #f0e6d9;
    display: block;
    object-fit: cover;
  }

  .media-card .info {
    padding: 10px 12px;
    background: white;
    font-size: 11px;
    color: #5c4636;
    min-height: 42px; /* 让信息区在只有尺寸+大小时也有稳定视觉重量，不显得空 */
    display: flex;
    align-items: center;
  }
  /* 当前阶段的元数据展示（尺寸 + 大小） */
  .media-card .meta {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 10.5px;
    color: #8c7563;
    width: 100%;
  }
  .media-card .dim {
    font-variant-numeric: tabular-nums;
  }
  .media-card .size {
    color: #a18a72;
  }

  /* 以下样式为未来恢复「当时在聊」+ 情绪标签预留，暂时不影响现有卡片 */
  .media-card .info-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    margin-bottom: 4px;
  }
  .media-card .date {
    font-size: 10px;
    color: #8c7563;
    flex-shrink: 0;
  }
  .media-card .context {
    font-size: 9.5px;
    color: #6b5b4f;
    line-height: 1.28;
    background: #f8f4ed;
    border-radius: 5px;
    padding: 2px 5px;
    margin-bottom: 5px;
    border-left: 2px solid #d4c9b8;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .media-card .context span { opacity: 0.88; }

  /* Safe visible placeholder for media cards (used during safe iteration) */
  .media-placeholder {
    width: 100%;
    aspect-ratio: 1;
    background: linear-gradient(135deg, #f0e6d9 0%, #e8dcc8 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #b8a48a;
    border-bottom: 1px solid #f0e6d9;
    transition: opacity 0.2s ease;
  }

  .media-placeholder.loading {
    animation: photo-loading-pulse 2.2s ease-in-out infinite;
  }

  @keyframes photo-loading-pulse {
    0%, 100% { opacity: 0.55; }
    50% { opacity: 0.9; }
  }
  .media-label {
    padding: 8px 12px;
    background: white;
    font-size: 12px;
    color: #5c4636;
  }

  .media-write-hint {
    position: absolute;
    bottom: 8px;
    right: 8px;
    background: rgba(255, 158, 177, 0.9);
    color: white;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 999px;
    opacity: 0;
    transition: opacity 0.2s ease;
    pointer-events: auto;
    z-index: 2;

    /* Button reset so it looks exactly like the old pill */
    border: none;
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
    cursor: pointer;
  }

  .media-card:hover .media-write-hint {
    opacity: 1;
  }

  .media-write-hint:hover {
    background: #ff9eb1;
  }

  /* Gentle keyboard focus ring matching the warm aesthetic */
  .media-write-hint:focus-visible {
    outline: 2px solid #ff9eb1;
    outline-offset: 2px;
    opacity: 1; /* ensure it's visible when focused via keyboard */
  }

  /* 右侧批注相关 */
  .anno-header { font-weight: 600; color: #5c4636; margin-bottom: 12px; font-size: 15px; }

  /* 让批注内容居中放置（体验优化），右侧面板仍可自由拖宽 */
  .anno-centered {
    max-width: 420px;
    margin: 0 auto;
    width: 100%;
    padding-left: 8px;
    padding-right: 8px;
    box-sizing: border-box;
  }

  /* 批注面板内空状态居中（垂直+水平） */
  .empty-state.centered-in-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 280px;
    text-align: center;
    padding: 24px 12px;
    color: #8c7563;
  }
  .target-hint { font-size: 11px; color: #8c7563; font-weight: normal; }
  .anno-card {
    background: white;
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    max-width: 100%;
    transition: background-color 0.3s ease, box-shadow 0.3s ease;
  }

  .anno-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 6px;
  }

  .edit-btn {
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 999px;
    border: 1px solid #f0e6d9;
    background: #fffaf0;
    color: #8c7563;
    cursor: pointer;
    flex-shrink: 0;
  }
  .edit-btn:hover {
    background: #f0e6d9;
  }

  .anno-actions {
    display: flex;
    gap: 4px;
    flex-shrink: 0;
  }

  .delete-btn {
    font-size: 11px;
    padding: 1px 8px;
    border-radius: 999px;
    border: 1px solid #f0e6d9;
    background: #fffaf0;
    color: #c25c6b;
    cursor: pointer;
    flex-shrink: 0;
  }
  .delete-btn:hover {
    background: #ffe4e1;
    border-color: #ff9eb1;
  }

  /* 温柔删除确认条 + 撤销提示（温暖可爱风格，复用现有 token） */
  .delete-confirm-bar {
    background: #fffaf0;
    border: 1px solid #f0e6d9;
    border-radius: 14px;
    padding: 10px 12px;
    margin: 8px 0;
    font-size: 12px;
    color: #5c4636;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }
  .confirm-actions {
    display: flex;
    gap: 6px;
  }
  .confirm-delete-btn {
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 999px;
    border: 1px solid #ff9eb1;
    background: linear-gradient(90deg, #ff9eb1, #f4a3b5);
    color: white;
    cursor: pointer;
  }
  .confirm-delete-btn:hover {
    filter: brightness(0.95);
  }

  .undo-toast {
    background: #fff7ed;
    border: 1px solid #ffedd5;
    border-radius: 14px;
    padding: 8px 12px;
    margin: 8px 0;
    font-size: 12px;
    color: #5c4636;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .undo-btn {
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 999px;
    border: 1px solid #a8e6cf;
    background: #e6f7f0;
    color: #3a6b57;
    cursor: pointer;
    flex-shrink: 0;
  }
  .undo-btn:hover {
    background: #d1f0e3;
  }
  .undo-close {
    margin-left: auto;
    font-size: 14px;
    color: #8c7563;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0 4px;
    line-height: 1;
  }

  /* 极简目标类型徽章（混合列表里最有价值的小细节） */
  .target-badge {
    font-size: 9px;
    padding: 1px 6px;
    border-radius: 999px;
    background: #f0e6d9;
    color: #8c7563;
    white-space: nowrap;
    flex-shrink: 0;
    margin-right: 6px;
    line-height: 1.3;
  }
  .target-badge.media {
    background: #e6f7f0;
    color: #3a6b57;
    max-width: 92px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .target-badge.message {
    background: #ffe4e1;
    color: #c25c6b;
  }
  .target-badge.slice {
    background: #f8f1eb;
    color: #8c7563;
  }

  .anno-card.newly-saved {
    background: #fff7ed;
    box-shadow: 0 0 0 3px #ffedd5;
  }
  .tags { display: flex; gap: 4px; margin-bottom: 6px; }
  .tag {
    font-size: 10px;
    background: #ffe4e1;
    color: #c25c6b;
    padding: 1px 7px;
    border-radius: 999px;
  }
  .anno-content { font-size: 13px; line-height: 1.5; color: #5c4636; }
  .add-form textarea {
    width: 100%;
    border: 1px solid #f0e6d9;
    border-radius: 14px;
    padding: 10px;
    font-size: 13px;
    resize: vertical;
    background: #fffaf0;
  }
  .tag-row { display: flex; flex-wrap: wrap; gap: 4px; margin: 8px 0; }
  .tag-btn {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 999px;
    border: 1px solid #f0e6d9;
    background: #fffaf0;
    color: #8c7563;
    cursor: pointer;
  }
  .tag-btn:hover { background: #ffe4e1; color: #c25c6b; }
  .save-btn {
    width: 100%;
    background: linear-gradient(90deg, #ff9eb1, #a8e6cf);
    color: white;
    border: none;
    padding: 10px;
    border-radius: 999px;
    font-size: 13px;
    cursor: pointer;
    margin-top: 4px;
  }
  /* 空状态和保存按钮（可进一步迁移） */
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #8c7563;
    font-size: 13px;
    line-height: 1.6;
  }
  .empty-icon { font-size: 42px; margin-bottom: 12px; }

  .form-actions {
    display: flex;
    gap: 8px;
    margin-top: 4px;
  }

  .form-context-hint {
    font-size: 11px;
    color: #c25c6b;
    margin-bottom: 4px;
    font-style: italic;
  }

  .cancel-btn {
    flex: 1;
    background: #f0e6d9;
    color: #5c4636;
    border: none;
    padding: 10px;
    border-radius: 999px;
    font-size: 13px;
    cursor: pointer;
  }

  .tag-btn.selected {
    background: #ffe4e1;
    color: #c25c6b;
    border-color: #ff9eb1;
  }
</style>
