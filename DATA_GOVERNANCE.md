# Data governance and interpretation

## Classification standard

Every displayed measure belongs to one of these classes:

1. **Official published measure**: a value published by Statistics Canada, the Government of Canada Job Bank, the Canada Revenue Agency, or the World Bank. The dashboard preserves the source unit and observation period.
2. **Derived calculation**: arithmetic performed locally from official published measures, such as annual basket cost, facilities per 100,000 population, rent burden, take-home estimate, or monthly money left.
3. **Scenario input**: a user-selected assumption such as household size, transportation cost, salary, expense growth, revenue, or cash reserves.
4. **Scenario score or recommendation**: a locally defined weighted comparison. It is not an official government or World Bank indicator.

## Dashboard register

| Dashboard | Official inputs | Derived outputs | Important limitation |
|---|---|---|---|
| Canada affordability and opportunity | 2025 metropolitan rents, 2025 Job Bank wages, provincial food prices | Estimated take-home, rent burden, monthly balance, score | Payroll credits and personal deductions are not modelled; grocery quantities and transportation costs are scenarios |
| Canadian healthcare access | ODHF facility records, latest quarterly provincial population | Facilities per 100,000, community concentration | Facility counts do not measure beds, staffing, capacity, quality, travel time, or wait times; only geocoded records are mapped |
| Newcomer settlement | Official rent, wage, food-price, and ODHF records | Household core costs, normalized components, settlement score | Mapped facility footprint is not healthcare access; score is not immigration or relocation advice |
| Food affordability | Monthly provincial food prices and latest annual median after-tax income | Representative basket, annual change, income burden, product contributions | Basket weights are a transparent scenario and are not the official CPI basket |
| Nonprofit sustainability | Statistics Canada nonprofit employment | Margin, runway, funding gap, stress-test matrix, risk label | Organization finances are user inputs and do not represent a specific nonprofit unless entered by that organization |
| Global cost and opportunity | World Bank PPP income, unemployment, inflation, and health spending | Normalized fingerprint and weighted score | Inflation measures price change, not the absolute cost-of-living level; country indicators are not city-level relocation costs |

## Source links

- [Statistics Canada table 34-10-0133-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3410013301)
- [Statistics Canada table 18-10-0245-02](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810024502)
- [Statistics Canada Open Database of Healthcare Facilities](https://www.statcan.gc.ca/en/lode/databases/odhf)
- [Statistics Canada table 36-10-0615-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610061501)
- [Government of Canada Job Bank wage data](https://open.canada.ca/data/en/dataset/adad580f-76b0-4502-bd05-20c125de9116)
- [Government of Canada Job Bank outlook data](https://open.canada.ca/data/en/dataset/b0e112e9-cf53-4e79-8838-23cd98debe5b)
- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation)

## Required use

These dashboards support exploration and planning. Users making financial, immigration, medical, housing, or organizational decisions must confirm the latest source publication and obtain qualified advice where appropriate.

