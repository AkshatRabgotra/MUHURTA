import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SlotCard from '@/components/SlotCard';
import type { Slot } from '@/types';

const mockSlot: Slot = {
  id: 'slot-123',
  start_utc: '2024-04-15T09:00:00Z',
  end_utc: '2024-04-15T09:30:00Z',
  score: 14.5,
  rank: 1,
  explanation_text: 'Favorable alignment of Rohini nakshatra and Amrit choghadiya.',
  reasons: [
    { factor: 'Nakshatra', value: 'Rohini', points: 4.5 },
    { factor: 'Choghadiya', value: 'Amrit', points: 6.0 },
    { factor: 'Weekday', value: 'Monday', points: 2.0 },
  ],
};

describe('SlotCard Component', () => {
  it('renders slot rank, score, and explanation', () => {
    render(<SlotCard slot={mockSlot} userTimezone="Asia/Kolkata" />);

    expect(screen.getByText('Rank #1')).toBeInTheDocument();
    expect(screen.getByText(/14.5 pts/i)).toBeInTheDocument();
    expect(
      screen.getByText('Favorable alignment of Rohini nakshatra and Amrit choghadiya.')
    ).toBeInTheDocument();
  });

  it('renders auspicious factors breakdown chips', () => {
    render(<SlotCard slot={mockSlot} />);

    expect(screen.getAllByText(/Rohini/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/Amrit/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/\(\+4.5\)/i)).toBeInTheDocument();
  });

  it('renders Add to Google Calendar button and feedback buttons', () => {
    render(<SlotCard slot={mockSlot} />);

    expect(
      screen.getByRole('button', { name: /\+ Add to Google Calendar/i })
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /thumbs up/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /thumbs down/i })).toBeInTheDocument();
  });
});
