export interface Speech {
  speech_id: number
  speech_content: string
  datestamp: string
  from_tribune: boolean
  speaker_name: string
  party_abbreviation: string
  party_name: string
}

export interface FilterOptions {
  speakers: { id: number; name: string; middle_name: string }[]
  parties: { id: number; name: string; abbr: string }[]
  from_tribune_options: boolean[]
  dates: string[]
}