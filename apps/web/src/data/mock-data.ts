import { 
  Series, 
  Story, 
  Child, 
  Family, 
  EveningSuggestion, 
  SharedMemory,
  SubscriptionStatus 
} from '@/types';

// Mock data for development - will be replaced by API calls

export const mockChildren: Child[] = [
  {
    id: 'child-1',
    name: 'נועה',
    age: 4,
    avatarUrl: undefined,
    createdAt: new Date('2024-01-15'),
  },
  {
    id: 'child-2', 
    name: 'איתי',
    age: 6,
    avatarUrl: undefined,
    createdAt: new Date('2024-01-15'),
  },
];

export const mockFamily: Family = {
  id: 'family-1',
  parentEmail: 'parent@example.com',
  children: mockChildren,
  members: [
    { id: 'member-1', name: 'אמא', role: 'parent' },
    { id: 'member-2', name: 'אבא', role: 'parent' },
    { id: 'member-3', name: 'סבתא רחל', role: 'grandparent' },
  ],
  createdAt: new Date('2024-01-15'),
};

export const mockSeries: Series[] = [
  {
    id: 'series-1',
    title: 'הרפתקאות הלילה של דובי',
    description: 'סדרה מרגיעה על דובי קטן שגילה שהלילה מלא בהפתעות טובות',
    coverUrl: '/placeholder.svg',
    ageRange: [3, 5],
    themes: ['דמיון', 'אומץ', 'שינה'],
    challenges: ['פחד מהחושך', 'קשיי הירדמות'],
    episodeCount: 8,
  },
  {
    id: 'series-2',
    title: 'הגן החדש של טלי',
    description: 'טלי מתחילה בגן חדש ולומדת על חברויות, שינויים והתחלות',
    coverUrl: '/placeholder.svg',
    ageRange: [3, 5],
    themes: ['חברות', 'שינוי', 'אומץ'],
    challenges: ['התחלת גן', 'חרדת פרידה'],
    episodeCount: 6,
  },
  {
    id: 'series-3',
    title: 'האח הקטן מגיע',
    description: 'סיפור על משפחה שמתרחבת ועל האהבה שגדלה איתה',
    coverUrl: '/placeholder.svg',
    ageRange: [2, 6],
    themes: ['משפחה', 'אהבה', 'שיתוף'],
    challenges: ['אח חדש', 'קנאה'],
    episodeCount: 5,
  },
];

export const mockStories: Story[] = [
  {
    id: 'story-1-1',
    seriesId: 'series-1',
    title: 'הכוכב הראשון',
    coverUrl: '/placeholder.svg',
    parentContext: 'בסיפור הזה דובי מגלה שכוכבים הם חברים שמחכים לו בלילה. זה יכול לעזור לילדים שמפחדים מהחושך.',
    content: [
      { type: 'text', content: 'דובי שכב במיטה החמה שלו. החדר היה חשוך, אבל משהו נוצץ בחלון.' },
      { type: 'text', content: '"מה זה?" שאל דובי בלחש.' },
      { type: 'text', content: 'זה היה כוכב קטן, מצמץ לו בידידותיות.' },
      { type: 'text', content: '"שלום, דובי," אמר הכוכב. "אני כאן כל לילה, שומר עליך."' },
      { type: 'text', content: 'דובי חייך. הוא לא ידע שיש לו חבר בשמיים.' },
      { type: 'text', content: 'מאותו לילה, דובי תמיד חיפש את הכוכב לפני שנרדם.' },
      { type: 'text', content: 'והכוכב תמיד היה שם, מצמץ לו לילה טוב.' },
    ],
    conversationStarters: [
      'איזה כוכב היית רוצה שישמור עליך?',
      'מה עוד יכול להיות חבר שלנו בלילה?',
    ],
    position: 1,
  },
  {
    id: 'story-1-2',
    seriesId: 'series-1',
    title: 'הצלילים של הלילה',
    coverUrl: '/placeholder.svg',
    parentContext: 'דובי לומד שצלילי הלילה הם חלק מהטבע ולא מפחידים. מתאים לילדים שמפחדים מרעשים בלילה.',
    content: [
      { type: 'text', content: 'הלילה היה שקט. או שלא?' },
      { type: 'text', content: 'דובי שמע רשרוש. "מי שם?" הוא שאל.' },
      { type: 'text', content: 'זה היה רק הרוח, מלטפת את העלים בעדינות.' },
      { type: 'text', content: 'אחר כך שמע ציוץ קטן. זה היה ציפור לילה, שרה שיר ערש.' },
      { type: 'text', content: 'דובי הבין - הלילה לא שקט. הוא מלא במוזיקה רכה.' },
      { type: 'text', content: 'הוא עצם את עיניו והקשיב לסימפוניה של הלילה.' },
    ],
    conversationStarters: [
      'אילו צלילים אתה שומע לפני שאתה נרדם?',
    ],
    position: 2,
  },
];

export const mockEveningSuggestion: EveningSuggestion = {
  type: 'continue',
  seriesId: 'series-1',
  storyId: 'story-1-2',
  title: 'הצלילים של הלילה',
  message: 'להמשיך עם הרפתקאות הלילה של דובי?',
};

export const mockSharedMemories: SharedMemory[] = [
  {
    id: 'memory-1',
    storyTitle: 'הכוכב הראשון',
    seriesTitle: 'הרפתקאות הלילה של דובי',
    childName: 'נועה',
    readAt: new Date('2024-01-20'),
  },
];

export const mockSubscription: SubscriptionStatus = {
  plan: 'trial',
  expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
  canCreateStories: false,
  maxChildren: 2,
  maxFamilyMembers: 4,
};

// Predefined topics for story creation
export const storyTopics = [
  { id: 'new-sibling', label: 'אח או אחות חדשים' },
  { id: 'starting-school', label: 'התחלת בית ספר' },
  { id: 'moving-house', label: 'מעבר דירה' },
  { id: 'making-friends', label: 'לעשות חברים חדשים' },
  { id: 'bedtime-fears', label: 'פחדים לפני השינה' },
  { id: 'separation', label: 'פרידה מהורים' },
  { id: 'sharing', label: 'לימוד שיתוף' },
  { id: 'emotions', label: 'הבנת רגשות' },
];
