// Shared Supabase config + client for every page.
// The anon (public) key is safe to expose; Row Level Security limits it to reads.
// To rotate or change projects, edit only these two lines.
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';

export const SUPABASE_URL = 'https://sfkrackwzluhtiqutqqy.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNma3JhY2t3emx1aHRpcXV0cXF5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5NDUxMzEsImV4cCI6MjA5NzUyMTEzMX0.8f6fO_3q6Nltcn0EPJQY1vJ1POzngwfzKHQLju2GOkQ';

export const sb = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// formatting helpers shared across pages
export const fmtPct = v => (v == null ? '—' : (v * 100).toFixed(1) + '%');
export const fmtNum = (v, d = 2) => (v == null ? '—' : Number(v).toFixed(d));
export const cls = v => (v > 0 ? 'pos' : v < 0 ? 'neg' : '');
