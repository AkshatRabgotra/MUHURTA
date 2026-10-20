import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import PlannerPage from '@/app/page';

describe('Planner Form', () => {
  it('renders heading, textarea input, and submit button', () => {
    render(<PlannerPage />);

    expect(screen.getByText('Find Your Auspicious Timing')).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/I want to sign my rental agreement/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Calculate Auspicious Times/i })
    ).toBeInTheDocument();
  });

  it('populates input when example chip is clicked', () => {
    render(<PlannerPage />);

    const chip = screen.getByText(/I want to sign my rental agreement next week/i);
    fireEvent.click(chip);

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toContain('I want to sign my rental agreement next week');
  });
});
