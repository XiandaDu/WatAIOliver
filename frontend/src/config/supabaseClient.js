
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY

const supabase = createClient(supabaseUrl, supabaseKey)
export default supabase
// Ensure that the environment variables are set correctly in your .env file