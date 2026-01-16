import { formatDistanceToNowStrict } from 'date-fns'

interface TimestampProps {
  value: string
}

export function Timestamp({ value }: TimestampProps) {
  const date = new Date(value)
  const label = Number.isNaN(date.getTime())
    ? 'inconnu'
    : formatDistanceToNowStrict(date, { addSuffix: true })

  return <span>{label}</span>
}
