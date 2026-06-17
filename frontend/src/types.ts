export interface MeetingListItem {
  id: number;
  title: string;
  created_at: string;
  duration: number;
  status: string;
  stage: string;
  num_speakers: number;
  num_action_items: number;
}

export interface Speaker {
  id: number;
  label: string;
  display_name: string | null;
}

export interface Segment {
  id: number;
  start: number;
  end: number;
  text: string;
  speaker_id: number | null;
  speaker_label: string | null;
  speaker_name: string | null;
}

export interface ActionItem {
  id: number;
  task: string;
  owner: string | null;
  deadline: string | null;
  completed: boolean;
}

export interface Summary {
  overview: string | null;
  attendees: string[];
  key_decisions: string[];
  discussion_points: string[];
  open_questions: string[];
  next_steps: string[];
}

export interface MeetingDetail {
  id: number;
  title: string;
  created_at: string;
  duration: number;
  status: string;
  stage: string;
  error: string | null;
  language: string | null;
  speakers: Speaker[];
  segments: Segment[];
  summary: Summary | null;
  action_items: ActionItem[];
  topics: string[];
}

export interface SearchMatch {
  meeting_id: number;
  meeting_title: string;
  type: string;
  speaker: string | null;
  start: number | null;
  end: number | null;
  text: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  answer: string;
  matches: SearchMatch[];
}

export interface AnalyticsOverview {
  total_meetings: number;
  total_duration: number;
  total_action_items: number;
  completed_action_items: number;
  completion_rate: number;
  speaking_time: { speaker: string; seconds: number; percentage: number }[];
  frequency: { period: string; count: number }[];
  top_topics: { topic: string; count: number }[];
}

export interface Health {
  status: string;
  model: string;
  embed_model: string;
  gemini_configured: boolean;
  diarisation_configured: boolean;
  whisper_model: string;
}
