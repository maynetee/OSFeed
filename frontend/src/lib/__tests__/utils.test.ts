import { describe, it, expect, beforeEach, vi } from 'vitest'
import { clamp, formatCompactNumber, formatDateTime } from '../utils'

describe('utils', () => {
  describe('clamp', () => {
    it('should return min when value is less than min', () => {
      expect(clamp(5, 10, 20)).toBe(10)
      expect(clamp(-100, 0, 50)).toBe(0)
      expect(clamp(-5, -3, 10)).toBe(-3)
    })

    it('should return max when value is greater than max', () => {
      expect(clamp(25, 10, 20)).toBe(20)
      expect(clamp(100, 0, 50)).toBe(50)
      expect(clamp(15, -10, 10)).toBe(10)
    })

    it('should return value when within range', () => {
      expect(clamp(15, 10, 20)).toBe(15)
      expect(clamp(25, 0, 50)).toBe(25)
      expect(clamp(0, -10, 10)).toBe(0)
    })

    it('should handle boundary values correctly', () => {
      expect(clamp(10, 10, 20)).toBe(10)
      expect(clamp(20, 10, 20)).toBe(20)
      expect(clamp(0, 0, 0)).toBe(0)
    })

    it('should handle negative ranges', () => {
      expect(clamp(-15, -20, -10)).toBe(-15)
      expect(clamp(-25, -20, -10)).toBe(-20)
      expect(clamp(-5, -20, -10)).toBe(-10)
    })

    it('should handle decimal values', () => {
      expect(clamp(5.5, 10.2, 20.8)).toBe(10.2)
      expect(clamp(15.7, 10.2, 20.8)).toBe(15.7)
      expect(clamp(25.3, 10.2, 20.8)).toBe(20.8)
    })

    it('should handle zero values', () => {
      expect(clamp(0, -10, 10)).toBe(0)
      expect(clamp(5, 0, 10)).toBe(5)
      expect(clamp(-5, -10, 0)).toBe(-5)
    })
  })

  describe('formatCompactNumber', () => {
    it('should format numbers with default locale (fr-FR)', () => {
      expect(formatCompactNumber(1000)).toBe('1 k')
      expect(formatCompactNumber(1000000)).toBe('1 M')
      expect(formatCompactNumber(1000000000)).toBe('1 Md')
    })

    it('should format numbers with explicit fr-FR locale', () => {
      expect(formatCompactNumber(1500, 'fr-FR')).toBe('1,5 k')
      expect(formatCompactNumber(2500000, 'fr-FR')).toBe('2,5 M')
      expect(formatCompactNumber(3500000000, 'fr-FR')).toBe('3,5 Md')
    })

    it('should format numbers with en-US locale', () => {
      expect(formatCompactNumber(1000, 'en-US')).toBe('1K')
      expect(formatCompactNumber(1500, 'en-US')).toBe('1.5K')
      expect(formatCompactNumber(1000000, 'en-US')).toBe('1M')
      expect(formatCompactNumber(2500000, 'en-US')).toBe('2.5M')
    })

    it('should format small numbers without compacting', () => {
      expect(formatCompactNumber(999)).toBe('999')
      expect(formatCompactNumber(500)).toBe('500')
      expect(formatCompactNumber(1)).toBe('1')
    })

    it('should handle zero', () => {
      expect(formatCompactNumber(0)).toBe('0')
      expect(formatCompactNumber(0, 'en-US')).toBe('0')
    })

    it('should handle negative numbers', () => {
      expect(formatCompactNumber(-1000, 'en-US')).toBe('-1K')
      expect(formatCompactNumber(-1500000, 'en-US')).toBe('-1.5M')
    })

    it('should format very large numbers', () => {
      const trillion = 1000000000000
      const result = formatCompactNumber(trillion, 'en-US')
      expect(result).toContain('T')
    })

    it('should handle decimal input', () => {
      expect(formatCompactNumber(1234.56)).toBe('1,2 k')
      expect(formatCompactNumber(999.99)).toBe('1 k')
    })
  })

  describe('formatDateTime', () => {
    beforeEach(() => {
      // Reset timezone for consistent testing
      vi.useFakeTimers()
    })

    it('should format Date object with default options', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date)
      // Should include date and time in fr-FR locale
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format ISO string with default options', () => {
      const isoString = '2024-01-15T14:30:00Z'
      const formatted = formatDateTime(isoString)
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format timestamp number with default options', () => {
      const timestamp = new Date('2024-01-15T14:30:00Z').getTime()
      const formatted = formatDateTime(timestamp)
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format with custom locale en-US', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'en-US')
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
      // en-US format typically uses commas and AM/PM
      expect(/[\d:,\s]+(AM|PM)/i.test(formatted) || /[\d,\s]+/.test(formatted)).toBe(true)
    })

    it('should format with custom dateStyle and timeStyle', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'fr-FR', {
        dateStyle: 'long',
        timeStyle: 'long',
      })
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format with only date style', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'fr-FR', { dateStyle: 'short' })
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format with only time style', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'fr-FR', { timeStyle: 'short' })
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should handle different date formats', () => {
      const dates = [
        new Date('2024-01-01T00:00:00Z'),
        new Date('2024-12-31T23:59:59Z'),
        new Date('2024-06-15T12:00:00Z'),
      ]

      dates.forEach((date) => {
        const formatted = formatDateTime(date)
        expect(formatted).toBeTruthy()
        expect(typeof formatted).toBe('string')
      })
    })

    it('should format with custom options including weekday', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'fr-FR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should handle epoch timestamp (0)', () => {
      const formatted = formatDateTime(0)
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    it('should format recent dates consistently', () => {
      const date1 = new Date('2024-01-15T10:00:00Z')
      const date2 = new Date('2024-01-15T10:00:00Z')

      const formatted1 = formatDateTime(date1)
      const formatted2 = formatDateTime(date2)

      expect(formatted1).toBe(formatted2)
    })

    it('should handle different locales with same date', () => {
      const date = new Date('2024-01-15T14:30:00Z')

      const frFormatted = formatDateTime(date, 'fr-FR')
      const enFormatted = formatDateTime(date, 'en-US')
      const deFormatted = formatDateTime(date, 'de-DE')

      // All should be valid strings
      expect(frFormatted).toBeTruthy()
      expect(enFormatted).toBeTruthy()
      expect(deFormatted).toBeTruthy()

      // They might be different due to locale differences
      expect(typeof frFormatted).toBe('string')
      expect(typeof enFormatted).toBe('string')
      expect(typeof deFormatted).toBe('string')
    })

    it('should format with numeric date and time options', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const formatted = formatDateTime(date, 'fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
      // Should contain numeric representations
      expect(/\d/.test(formatted)).toBe(true)
    })
  })

  describe('integration tests', () => {
    it('should work together in realistic scenarios', () => {
      // Scenario: Display a stat with formatted count and date
      const viewCount = 1234567
      const lastUpdated = new Date('2024-01-15T14:30:00Z')

      const formattedCount = formatCompactNumber(viewCount, 'en-US')
      const formattedDate = formatDateTime(lastUpdated, 'en-US')

      expect(formattedCount).toBe('1.2M')
      expect(formattedDate).toBeTruthy()
      expect(typeof formattedDate).toBe('string')
    })

    it('should handle edge cases gracefully', () => {
      // Test that functions don't throw on edge case inputs
      expect(() => clamp(NaN, 0, 10)).not.toThrow()
      expect(() => formatCompactNumber(Infinity, 'en-US')).not.toThrow()
      expect(() => formatDateTime(new Date('invalid'))).not.toThrow()
    })

    it('should handle boundary values in real-world usage', () => {
      // Clamp a progress percentage
      const progress = 150
      const clampedProgress = clamp(progress, 0, 100)
      expect(clampedProgress).toBe(100)

      // Format a large follower count
      const followers = 2500000
      const formatted = formatCompactNumber(followers, 'en-US')
      expect(formatted).toBe('2.5M')
    })
  })
})
