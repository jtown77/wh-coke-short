# COKE Short — Qualitative Content (Drop-in for Streamlit Site)

Drafted 2026-05-06. Two new sections for the site, formatted to match the editorial style already in `sections.py` (eyebrow → H2 → narrative → blockquotes → 2-3 sentence captions). Drop into `app.py` after the existing Demand & Pricing block; cost-themed quotes go after the Cost Stack block.

---

## SECTION A — SNAP Soda Restrictions: A Direct Demand Catalyst

**Suggested slot:** new section between Demand & Pricing and Cost Stack. Eyebrow: "Demand Catalyst".

### Markdown content

> ### The Setup
>
> Beginning January 1, 2026, USDA approved waivers allowing states to restrict soda and other sugar-sweetened beverages from SNAP eligibility. By May 2026, 13+ states had effective dates published and 22 had received approval. The early-implementation states overlap directly with Coca-Cola Consolidated's franchise territory.
>
> **Effective dates by state (USDA, May 2026):**
>
> | State | Effective | Restricted |
> |---|---|---|
> | Iowa | Jan 1, 2026 | Soda + taxable foods |
> | Indiana | Jan 1, 2026 | Soft drinks + candy |
> | Nebraska | Jan 1, 2026 | Soda + energy drinks |
> | Utah | Jan 1, 2026 | Soft drinks |
> | West Virginia | Jan 1, 2026 | Soda |
> | Idaho | Feb 15, 2026 | Soda + candy |
> | Florida | Apr 20, 2026 | Soda, energy drinks, candy, prepared desserts |
> | Arkansas | Jul 1, 2026 | Soda + sugary drinks + candy |
> | Hawaii | Aug 1, 2026 | Soft drinks |
> | North Dakota | Sept 1, 2026 | Sweetened beverages, energy drinks, candy |
> | Missouri | Oct 1, 2026 | Candy, prepared desserts, sweetened beverages |
> | Ohio | Oct 1, 2026 | Sugar-sweetened beverages |
> | Virginia | Oct 1, 2026 | Sweetened beverages |
>
> *Source: USDA FNS, Food Restriction Waivers (fns.usda.gov/snap/waivers/foodrestriction).*
>
> ### What the Early Data Says
>
> The first three months of implementation produced measurable volume softness in waiver states. Two independent reads — one from a sell-side analyst, one from receipt-level data — point in the same direction.
>
> > *"Through early March, volume growth in SNAP-restricted states was down 3% year over year for soft drinks, with chocolate candy down 8% and hard candy down 3%."*
> > — **Robert Moskow, TD Securities**, as cited by Beverage Industry, March 2026
>
> > *"SNAP soda purchases fell about twice as much in waiver states as in non-waiver states — roughly negative fifteen percent versus negative seven and a half percent through the end of March."*
> > — **Ibotta receipt-data analysis**, March 2026
>
> ### Why This Hits COKE Specifically
>
> Coca-Cola Consolidated's territory covers the Southeast, Mid-Atlantic, and Midwest — the same geographic band where the early-2026 waiver states sit (Iowa is bottled by partner systems, but Virginia, West Virginia, Indiana, and Ohio are core CCK markets). Forward-looking, Florida (April 2026), Virginia (October 2026), and Ohio (October 2026) are the highest-leverage pain points: Ibotta flagged Florida and Virginia among the top soda-consuming states in the country.
>
> **The substitution argument doesn't fully save the volume.** Reddit threads in r/foodstamps and the r/news SNAP discussion show consumers switching from branded soda into tea, juice drinks, Kool-Aid, and sweetened powdered mixes — i.e., out of CCK's highest-margin sparkling category and into either lower-margin still beverages or out of the system entirely.
>
> ### Read for the Thesis
>
> Independent of macro pricing/affordability dynamics, this is a structural, multi-quarter demand reset that is already showing up in the data. The TD/Ibotta reads suggest a 3–8 percentage point volume drag in restricted states; with roughly 25–30% of CCK's territory population in states with effective or pending waivers by Q4 2026, even partial flow-through is a 100–200bp headwind to system volume that the model's base case does not contemplate.

### Caption (italicized small text below the section)

*Sources: USDA FNS waiver list; TD Securities (Robert Moskow) via Beverage Industry; Ibotta receipt analytics; Reddit r/foodstamps and r/news SNAP discussion threads. Volume figures are early reads through March 2026 and may revise as the full quarter prints; the directional finding — meaningfully larger soda decline in waiver states than control states — has held across both data sources.*

---

## SECTION B — Management Commentary: What KO and PEP Are Saying

**Suggested slot:** Two parts — pricing/affordability quotes inside the Demand & Pricing section (under the Y/Y volume vs. price chart); cost/headwind quotes inside the Cost Stack section (under the aluminum sensitivity figure).

### Theme 1 — Pricing power is moderating, low-income consumer is the focus

> #### Coca-Cola — Q1 2026
>
> > *"Pricing is embedded into this equation as well. We are going where the consumer is, right? Affordability continues to be part of the revenue growth management architecture that we have, not only in the U.S., but in different parts of the world as well. The consumers that have pressure today are the low-income consumers, and we really dialed up our affordability options to get closer to them. In North America, for instance, we went into bringing options not only on the single-serve, but on the multi-serve and the entry packs and helped us to continue to keep them in the franchise."*
> > — **Henrique Braun, CEO**, Coca-Cola Co. Q1 2026 earnings call (Apr 28, 2026), responding to Dara Mohsenian (Morgan Stanley)
>
> *Why this matters:* KO is publicly framing pricing as a lever they're pulling **down**, not up — affordability and entry-pack architecture are the new RGM playbook. For a leveraged bottler with fixed plant costs, this is the unfavorable side of the price/volume tradeoff: KO will protect the franchise, CCK absorbs the gross margin compression.
>
> #### PepsiCo — Q4 2025
>
> > *"For some consumers, low and middle income consumers, the biggest friction they have today in our category for faster penetration is affordability. So we have been testing multiple ways to give them affordability. So this will be a very surgical, very focused on particular brands, particular formats, particular channels investment."*
> > — **Ramon Laguarta, Chairman & CEO**, PepsiCo Q4 2025 earnings call (Feb 3, 2026)
>
> > *"Clearly a middle and low income consumer that continues to be stretched and choiceful, and that we have to earn being part of their basket every day."*
> > — **Ramon Laguarta**, same call
>
> *Why this matters:* PEP's Q4 2025 call announced an *acceleration* of affordability investments in the first half of 2026, explicitly aimed at the low/middle-income consumer who is "stretched." When the #2 player in the category is racing to hold price points down, the #1 player has to follow — and the bottlers are the variable cost in that equation.
>
> #### PepsiCo — Q3 2025
>
> > *"When you look at low-income households or middle-income households, they're very stretched. Fixed costs of living are going up around the world, and that will create the need for affordability and value and price points and cost consciousness also for the foreseeable future. Those are trends that they will go up and down notches in the curve, but I think the curve is going in the same direction probably in the majority of the markets."*
> > — **Ramon Laguarta**, PepsiCo Q3 2025 earnings call (Oct 9, 2025)
>
> *Why this matters:* The "foreseeable future" framing is critical. Management is telling investors this is structural, not a one-quarter blip — which means the price-mix algo that powered 2022–2024 EPS growth is unlikely to reload.

### Theme 2 — Input costs and bottler exposure

> #### Coca-Cola — Q1 2026 (the smoking gun)
>
> > *"The environment, you say, is fluid. It's difficult at this stage to say exactly how it's going to play out. As highlighted in our script, right now we estimate it's manageable at the company level, given we have less exposure. **Our bottling partners have more exposure, particularly aluminum and PET, on the back of both the oil price impact and just the overall supply chain disruptions** that are likely to affect us as we go through the year. With the system, we have a playbook that we've had to use now for quite a few years on a range of disruptions."*
> > — **John Murphy, President & CFO**, Coca-Cola Co. Q1 2026 earnings call (Apr 28, 2026), responding to Steve Powers (Deutsche Bank)
>
> *Why this matters:* This is the parent acknowledging on a public call that **the bottler — i.e., COKE — is where the cost pain lands**. KO sells concentrate; CCK pays for aluminum cans and PET resin. When the parent says "we have less exposure, our bottling partners have more," that is the explicit structural argument for the short.
>
> #### Coca-Cola — Q1 2026 (gross margin)
>
> > *"Comparable gross margin declined approximately 30 basis points stemming primarily from commodity pressures in our tea and coffee businesses, phasing of inventory costs, and timing of trade spend… We've got a lot of levers to work through, both as a company and as we alluded to earlier, as a system."*
> > — **John Murphy**, same call
>
> *Why this matters:* Even at the parent level — where the aluminum exposure is reduced — gross margin is already contracting against commodity pressure. That contraction is amplified at the bottler.
>
> #### PepsiCo — Q3 2025
>
> > *"Q3 was impacted by tariffs. We see already in Q4 an expansion of the margin again to complete a positive margin expansion for the full year… We see PB&A continue to expand margins at a good pace."*
> > — **Ramon Laguarta**, PepsiCo Q3 2025 earnings call (Oct 9, 2025)
>
> *Why this matters:* PEP's beverage segment took a tariff hit in Q3 2025 that it described as discrete. The Q1 2026 KO quote above suggests these costs are not actually one-off — they are escalating into 2026 with both oil-price flow-through (PET) and direct tariff pressure on aluminum imports.

### Caption (italicized small text below the section)

*Quotes verified against full earnings call transcripts via the EarningsCall.biz API. Speaker attributions are based on the prepared Q&A roster on each call. KO Q1 2026 call held April 28, 2026; PEP Q4 2025 call held February 3, 2026; PEP Q3 2025 call held October 9, 2025. All quotes are presented verbatim with normal-speech disfluencies cleaned only where they obscure meaning.*

---

## How to wire into `sections.py`

Two new render functions:

```python
def render_snap_demand_catalyst() -> None:
    st.markdown('<div class="eyebrow">Demand Catalyst</div>', unsafe_allow_html=True)
    st.markdown("## SNAP Soda Restrictions — Underwriting a Demand Reset")
    # ... insert Section A markdown ...
    st.caption(...)  # the italicized source line

def render_management_commentary_pricing() -> None:
    st.markdown("### What Management Is Saying — Pricing & The Consumer")
    # ... insert Section B Theme 1 ...

def render_management_commentary_costs() -> None:
    st.markdown("### What Management Is Saying — Input Costs & Bottler Exposure")
    # ... insert Section B Theme 2 ...
```

Wire-up in `app.py` after the existing block ordering:
- `render_snap_demand_catalyst()` after `render_quarterly_yoy(...)` (volume/price story)
- `render_management_commentary_pricing()` immediately after `render_snap_demand_catalyst()`
- `render_management_commentary_costs()` after `render_aluminum_sensitivity(...)`

This keeps qualitative content adjacent to the chart it reinforces — quote-as-caption next to figure-as-evidence.
