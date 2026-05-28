// src/lib/mockData.ts
// 大量高质量测试数据 - 用于验证虚拟滚动、分隔条等真实组件行为
// 模拟 2025 年 3-4 月的聊天记录

export interface Slice {
  id: string;
  title: string;
  startDate: string;
  endDate: string;
  messageCount: number;
  eventType: string;
}

export interface Message {
  id: string;
  sliceId: string;
  time: string;           // HH:mm
  fromMe: boolean;
  type: 'text' | 'image' | 'video' | 'voice' | 'sticker';
  content: string;        // 文字内容或媒体文件名占位
}

export interface MediaItem {
  id: string;
  title: string;
  url: string;
  date: string;
  type: 'image' | 'video';
}

export interface Annotation {
  id: string;
  targetType: 'message' | 'media' | 'slice';
  targetId: string;
  content: string;
  tags: string[];
}

// ==================== SLICES（事件片段） ====================
export const slices: Slice[] = [
  { id: 'slice_0308', title: '3月8日 日常周末', startDate: '2025-03-08', endDate: '2025-03-08', messageCount: 87, eventType: '日常' },
  { id: 'slice_0310', title: '3月10日 争执后和好', startDate: '2025-03-10', endDate: '2025-03-10', messageCount: 142, eventType: '争吵' },
  { id: 'slice_0315', title: '3月15日 普通周末聊天', startDate: '2025-03-15', endDate: '2025-03-15', messageCount: 68, eventType: '日常' },
  { id: 'slice_0316', title: '3月16日 早安与加班', startDate: '2025-03-16', endDate: '2025-03-16', messageCount: 53, eventType: '日常' },
  { id: 'slice_0320', title: '3月20-21日 三亚旅行', startDate: '2025-03-20', endDate: '2025-03-21', messageCount: 234, eventType: '旅行' },
  { id: 'slice_0322', title: '3月22日 旅行回忆', startDate: '2025-03-22', endDate: '2025-03-22', messageCount: 91, eventType: '旅行' },
  { id: 'slice_0328', title: '3月28日 纪念日', startDate: '2025-03-28', endDate: '2025-03-28', messageCount: 156, eventType: '纪念日' },
  { id: 'slice_0401', title: '4月1日 愚人节整蛊', startDate: '2025-04-01', endDate: '2025-04-01', messageCount: 74, eventType: '有趣' },
  { id: 'slice_0405', title: '4月5日 清明与想念', startDate: '2025-04-05', endDate: '2025-04-05', messageCount: 112, eventType: '想念' },
];

// ==================== MESSAGES（大量测试消息） ====================
// 重点：slice_0320（三亚旅行）有 180+ 条，专门测试虚拟滚动
export const messages: Message[] = [
  // === slice_0308 日常周末（较少） ===
  { id: 'm_0308_001', sliceId: 'slice_0308', time: '09:14', fromMe: false, type: 'text', content: '早安宝贝～睡醒了吗？' },
  { id: 'm_0308_002', sliceId: 'slice_0308', time: '09:15', fromMe: true, type: 'text', content: '刚醒，昨晚好香啊' },
  { id: 'm_0308_003', sliceId: 'slice_0308', time: '09:17', fromMe: false, type: 'image', content: 'IMG_0308_0917.jpg' },
  { id: 'm_0308_004', sliceId: 'slice_0308', time: '10:42', fromMe: true, type: 'text', content: '哈哈哈这表情包绝了' },
  { id: 'm_0308_005', sliceId: 'slice_0308', time: '10:43', fromMe: false, type: 'sticker', content: 'sticker_laugh.png' },

  // === slice_0310 争执后和好（中等量） ===
  { id: 'm_0310_001', sliceId: 'slice_0310', time: '21:03', fromMe: false, type: 'text', content: '对不起，我刚才不该说那些话' },
  { id: 'm_0310_002', sliceId: 'slice_0310', time: '21:05', fromMe: true, type: 'text', content: '我也有错……我们别吵了好吗' },
  { id: 'm_0310_003', sliceId: 'slice_0310', time: '21:08', fromMe: false, type: 'voice', content: 'voice_0310_2108.amr' },
  { id: 'm_0310_004', sliceId: 'slice_0310', time: '21:12', fromMe: true, type: 'text', content: '我现在就想抱抱你' },
  // ... 省略部分，实际会生成更多

  // === slice_0315（当前默认） ===
  { id: 'm_0315_001', sliceId: 'slice_0315', time: '08:55', fromMe: false, type: 'text', content: '早安！今天想吃什么？' },
  { id: 'm_0315_002', sliceId: 'slice_0315', time: '08:56', fromMe: true, type: 'text', content: '想吃你做的蛋炒饭' },
  { id: 'm_0315_003', sliceId: 'slice_0315', time: '09:12', fromMe: false, type: 'image', content: 'IMG_0315_0912.jpg' },
  { id: 'm_0315_004', sliceId: 'slice_0315', time: '09:13', fromMe: true, type: 'text', content: '这猫也太可爱了吧！！！' },
  { id: 'm_0315_005', sliceId: 'slice_0315', time: '12:40', fromMe: false, type: 'voice', content: 'voice_0315_1240.amr' },
  { id: 'm_0315_006', sliceId: 'slice_0315', time: '14:22', fromMe: true, type: 'sticker', content: 'sticker_heart.png' },
  { id: 'm_0315_007', sliceId: 'slice_0315', time: '18:05', fromMe: false, type: 'text', content: '今天加班好累啊……想你了' },
  { id: 'm_0315_008', sliceId: 'slice_0315', time: '20:33', fromMe: true, type: 'image', content: 'IMG_0315_2033.jpg' },

  // === slice_0320 三亚旅行（重头戏：大量消息，测试虚拟滚动） ===
  // 这里生成 180+ 条真实感的聊天
  { id: 'm_0320_001', sliceId: 'slice_0320', time: '07:12', fromMe: false, type: 'text', content: '起床啦！飞机还有两个小时' },
  { id: 'm_0320_002', sliceId: 'slice_0320', time: '07:13', fromMe: true, type: 'text', content: '啊啊啊我还没打包好！！' },
  { id: 'm_0320_003', sliceId: 'slice_0320', time: '07:15', fromMe: false, type: 'sticker', content: 'sticker_cry.png' },
  { id: 'm_0320_004', sliceId: 'slice_0320', time: '09:45', fromMe: true, type: 'image', content: 'IMG_0320_airport.jpg' },
  { id: 'm_0320_005', sliceId: 'slice_0320', time: '09:46', fromMe: false, type: 'text', content: '到了吗？安全第一哦' },
  // ... 继续大量真实对话
  { id: 'm_0320_050', sliceId: 'slice_0320', time: '16:20', fromMe: true, type: 'text', content: '海边好美！照片发给你看' },
  { id: 'm_0320_051', sliceId: 'slice_0320', time: '16:21', fromMe: false, type: 'image', content: 'IMG_0320_sea1.jpg' },
  { id: 'm_0320_052', sliceId: 'slice_0320', time: '16:22', fromMe: true, type: 'text', content: '哇这光线绝了' },
  { id: 'm_0320_100', sliceId: 'slice_0320', time: '21:30', fromMe: false, type: 'voice', content: 'voice_0320_2130.amr' },
  { id: 'm_0320_101', sliceId: 'slice_0320', time: '21:35', fromMe: true, type: 'text', content: '听你的声音好想你' },
  { id: 'm_0320_150', sliceId: 'slice_0320', time: '23:55', fromMe: false, type: 'text', content: '晚安，我的旅行伴侣' },
  { id: 'm_0320_151', sliceId: 'slice_0320', time: '23:56', fromMe: true, type: 'text', content: '晚安，爱你' },

  // 继续填充更多 slice 的消息（为了真实感）
  { id: 'm_0322_001', sliceId: 'slice_0322', time: '10:05', fromMe: false, type: 'text', content: '回想昨天的日落真的太美了' },
  { id: 'm_0322_002', sliceId: 'slice_0322', time: '10:06', fromMe: true, type: 'image', content: 'IMG_0322_sunset.jpg' },
  // ... 省略，实际生成时会写更多

  { id: 'm_0328_001', sliceId: 'slice_0328', time: '08:00', fromMe: false, type: 'text', content: '生日快乐！！！' },
  { id: 'm_0328_002', sliceId: 'slice_0328', time: '08:01', fromMe: true, type: 'sticker', content: 'sticker_cake.png' },
];

// 为了演示虚拟滚动，这里手动补充 slice_0320 的大量消息（实际项目中可以用脚本生成）
const travelMessages: Message[] = [];
for (let i = 10; i < 180; i++) {
  const hour = 8 + Math.floor(i / 12);
  const min = (i % 12) * 5;
  const time = `${hour.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`;
  const fromMe = i % 3 !== 0;
  const type = i % 7 === 0 ? 'image' : (i % 11 === 0 ? 'voice' : 'text');
  
  let content = '';
  if (type === 'text') {
    const texts = [
      '这里好漂亮！', '我想你了', '快来陪我', '海水好蓝', 
      '今天吃了超好吃的芒果', '你猜我在想什么', '累但开心', 
      '照片拍得怎么样？', '晚安我的宝贝'
    ];
    content = texts[i % texts.length];
  } else if (type === 'image') {
    content = `IMG_0320_${(100 + i).toString().padStart(4, '0')}.jpg`;
  } else {
    content = `voice_0320_${(200 + i).toString().padStart(4, '0')}.amr`;
  }

  travelMessages.push({
    id: `m_0320_${i.toString().padStart(3, '0')}`,
    sliceId: 'slice_0320',
    time,
    fromMe,
    type: type as any,
    content
  });
}

messages.push(...travelMessages);

// ==================== MEDIA ====================
export const mediaItems: MediaItem[] = [
  { id: 'med_001', title: '机场自拍', url: 'https://picsum.photos/id/1011/300/300', date: '2025-03-20', type: 'image' },
  { id: 'med_002', title: '海边日落', url: 'https://picsum.photos/id/1016/300/300', date: '2025-03-20', type: 'image' },
  { id: 'med_003', title: '你睡着了', url: 'https://picsum.photos/id/1005/300/300', date: '2025-03-21', type: 'image' },
  { id: 'med_004', title: '椰子树', url: 'https://picsum.photos/id/201/300/300', date: '2025-03-20', type: 'image' },
  // 补充更多用于测试瀑布流
  ...Array.from({ length: 42 }, (_, i) => ({
    id: `med_${(100 + i).toString().padStart(3, '0')}`,
    title: `旅行照片 ${i + 1}`,
    url: `https://picsum.photos/id/${(1000 + i) % 200}/300/300`,
    date: i < 20 ? '2025-03-20' : '2025-03-21',
    type: (i % 5 === 0 ? 'video' : 'image') as 'image' | 'video'
  }))
];

// ==================== ANNOTATIONS ====================
export const annotations: Annotation[] = [
  {
    id: 'ann_001',
    targetType: 'message',
    targetId: 'm_0320_050',
    content: '那天夕阳真的太美了，我偷偷拍了你看海的背影',
    tags: ['甜蜜', '纪念']
  },
  {
    id: 'ann_002',
    targetType: 'media',
    targetId: 'med_002',
    content: '这张照片是她偷拍的，那天我穿了她最喜欢的白衬衫',
    tags: ['感动', '甜蜜']
  },
  {
    id: 'ann_003',
    targetType: 'slice',
    targetId: 'slice_0320',
    content: '三亚这趟旅行是我们在一起后最开心的一段时光',
    tags: ['纪念', '旅行']
  },
  {
    id: 'ann_004',
    targetType: 'message',
    targetId: 'm_0310_001',
    content: '吵架后她主动道歉的样子让我心软了好久',
    tags: ['争吵', '感动']
  }
];

// 再随机补充一些批注
for (let i = 5; i < 18; i++) {
  const randomMsg = messages[Math.floor(Math.random() * messages.length)];
  annotations.push({
    id: `ann_${i.toString().padStart(3, '0')}`,
    targetType: 'message',
    targetId: randomMsg.id,
    content: '写下此刻的心情…（测试批注 ' + i + '）',
    tags: ['甜蜜', '日常', '纪念'].slice(0, (i % 3) + 1)
  });
}
