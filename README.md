# Rideshare Analysis

I've driven for Uber and Lyft since 2018. Somewhere along the way I realized
I was sitting on a pretty detailed record of my own work — every trip, every
payment, every mile — and nobody had ever actually sat down and worked out
what the job pays once you account for all of it.

So I pulled my data and did it myself.

## What's here

This is a case study built from my real driving data between January 2023
and May 2026:

- 25,549 completed trips
- 7,876 hours clocked
- 158,940 miles driven
- Data pulled from four sources: Uber's trip and payment exports, Lyft's
  ride and session exports, and Gridwise (which tracks total time on the
  clock, including the unpaid waiting and driving-to-pickup that the apps
  leave out)

The four sources didn't agree with each other. Getting them to tell one
consistent story was most of the work.

## A few things I found

- My real hourly rate is about $41.61 — less than half the "$95/hour" the
  Uber app implies, because the app only counts time with a passenger in
  the car.
- Uber's cut of each fare has roughly doubled since I started, from about
  17% to 44%. My hourly pay stayed flat anyway, which means I've had to get
  more efficient just to break even with where I was.
- Airport trips pay about 2.7x a normal trip, and I almost never take them.

## How it was built

Python and Pandas for all the data work, Matplotlib and Chart.js for the
charts. The write-up is a single self-contained HTML page.

## See it live

[Link goes here once Pages is set up — see Step 4]

## Notes

All the earnings numbers are net of platform fees and cross-checked against
more than one source. Nothing in the headline figures is estimated. The raw
data isn't in this repo because it's my personal financial and trip history,
but the analysis approach is described in the case study itself.
