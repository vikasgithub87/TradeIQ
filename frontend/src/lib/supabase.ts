/**
 * supabase.ts — Supabase client singleton
 */
import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string) || ''
const supabaseKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string) || ''

const isValid = supabaseUrl.startsWith('https://') && supabaseKey.length > 20

let client: SupabaseClient
try {
  client = createClient(supabaseUrl || 'https://example.supabase.co', supabaseKey || 'x')
} catch {
  client = createClient('https://example.supabase.co', 'x')
}

export const supabase = client
export const isSupabaseConfigured = isValid
