# PEST analysis: quantum computing

**Guiding question.** The patent analysis raises one question: *why did quantum computing patenting take off after 2015, and why is it led by the United States and China?* Each factor below gives part of the answer and ends with what it means for Dell.

**What the patent data shows.** Patent families in the sector grew by 34% a year between 2010 and 2022, against 6% for patenting as a whole. The number of active applicants rose from 189 in 2015 to 1,102 in 2022.

## Political

Quantum computing is a national-security issue because a large enough quantum computer could break the public-key encryption that protects classified information and financial transactions. Governments therefore treat it as a strategic technology:

- By 2021, 17 countries had a national quantum initiative or strategy [1].
- By November 2025, 18 OECD countries and the European Union had adopted one [2].
- The US passed the National Quantum Initiative Act in 2018.

Defending against the threat is a separate field, post-quantum cryptography. It means new *classical* algorithms that quantum computers cannot break, which NIST standardised in 2024. Dell already ships it: quantum-resistant firmware protection in its 2026 commercial PCs [3], and post-quantum algorithms in its BSAFE cryptographic libraries [4].

The race is led by the US and China, but each leads in different areas. China claims over $15 billion in public funding for quantum research, which offsets the US advantage in private funding [5]. US-based quantum companies raised close to $5 billion between 2012 and 2024, the most of any country. The US is "the clear leader in quantum computing research quality and impact" and is ahead in commercialising quantum processors. China leads in quantum communication, especially satellite-based systems, and in patents [6].

Our data reflects this public effort:

- Universities and government bodies account for about 26% of the links between applicants and patent families.
- Chinese public institutions such as USTC, Tsinghua University, the Chinese Academy of Sciences and State Grid are among the top 25 applicants.
- China's patent office receives 27% of all applications in the sector, the largest share of any office.

US–China tension also affects supply chains. In 2023, Michael Dell said the company was moving component sourcing away from China because its customers asked for diversification. At the time, Dell was one of the three largest computer vendors in China [7].

*For Dell:* buying or partnering with a Chinese firm, such as Origin Quantum, QuantumCTek or Baidu, carries high political and export-control risk. Realistic targets are in the US, Canada and Europe.

## Economic

Investment is rising quickly but the market is still small:

- Quantum computing firms raised $1.6 billion in publicly announced investment in 2024 [8].
- More than 40 quantum processors are now sold commercially by at least two dozen manufacturers [8].
- Quantum still accounts for less than 1% of global venture capital, and no machine yet meets the needs of large-scale applications [8].
- McKinsey estimates that quantum technologies as a whole could be worth up to $198 billion by 2040, with quantum computing at $45–131 billion. These are scenario ranges, not point forecasts [9].

Our data shows the market is young and open:

- **Little concentration.** The four largest applicants hold only 9% of patent families.
- **Strong entry.** Seven of the 30 largest applicants first entered the sector in 2015 or later. Origin Quantum, a Chinese firm that filed its first patent in 2018, is already second with 560 families, behind IBM's 598. IonQ (122) and Quantinuum (83) are other recent entrants.
- **High exit.** Between 2014 and 2019, 38–54% of each year's active applicants never filed in the sector again.

*For Dell:* there are many small firms to choose from, but many will not survive. Look for entrants with strong patent records that are still filing.

## Social

The sector is short of skilled people. McKinsey found only one qualified candidate for every three quantum job openings, and forecast in 2022 that up to half of quantum jobs could remain unfilled by 2025 [10]. In the US, demand for quantum-skilled workers has nearly tripled since 2018 [6]. New roles are appearing, such as quantum engineers, quantum software specialists and quantum-algorithm researchers [11].

Public opinion is a second social factor. In an October 2024 survey of 1,375 US residents, 24% said they were nervous about the data-security and cryptography uses of quantum technology [6].

Our data shows two related patterns:

- Universities are among the largest applicants, which shows that the skills still sit mainly in academia.
- Between 2020 and 2022, about 290–310 organisations a year filed their first patent ever in this sector. Many of them are probably university spin-offs and start-ups.

Quantum technology may also widen the gap between rich countries that can afford national programmes and poorer countries that cannot, sometimes called the "quantum divide" **[source needed]**.

*For Dell:* buying a firm mainly for its team, or partnering with universities, may be the quickest way to get quantum skills.

## Technological

Quantum computing is moving from laboratory research towards engineering, but it is not yet mature. The main obstacle has been noise, which makes qubits unreliable. In December 2024, Google's Willow chip showed for the first time that the error rate falls as more qubits are added to an error-correcting code [12]. This is the condition for running longer and deeper circuits.

Integration with classical computers is now a technical focus of its own. NVIDIA's NVQLink platform connects GPUs directly to the FPGAs that control quantum processors. In March 2026, Dell validated latency below 4 microseconds between its PowerEdge servers and those FPGAs using NVQLink [13].

Our data shows where development is concentrated. Comparing 2013–2017 with 2018–2022:

- General quantum computing (`G06N10/00`): +2,624%
- Programming (`G06N10/80`): +945%
- Models (`G06N10/20`): +937%
- Physical realisations (`G06N10/40`): +734%
- Error correction (`G06N10/70`): +646%
- Quantum key distribution (`H04B10/70`): +353%
- Encryption-key management (`H04L9/08`): +293%, the largest group with 2,659 families

Firms also protect these inventions widely:

- 29% of families are filed through the international PCT route, against 12% for all patents.
- 72% are granted, against 48%.

*For Dell:* the strongest fit is the layer joining quantum and classical computing (servers, control systems, software) rather than building qubits, and the NVQLink work already puts Dell there.

## Conclusion

The take-off after 2015 follows government strategies and funding from 2018 onward, private investment in start-ups, and progress on error correction. The US leads in companies and private capital. China leads in public funding and patent filings. Our patent data understates China, because 47% of applicant records have no country and most of these are likely Chinese filings.

## References

1. Nextgov (2021). *National quantum leaders contemplate current investments and future innovation.* https://nextgov.com/emerging-tech/2021/05/national-quantum-leaders-contemplate-current-investments-and-future-innovation/174197/
2. OECD (2026). *Quantum technologies and the role of governments and policy.* https://www.oecd.org/en/blogs/2026/01/quantum-technologies-and-the-role-of-governments-and-policy-in-kickstarting-the-second-revolution.html
3. Dell Technologies. *Quantum resilience, built in.* https://www.dell.com/en-us/blog/quantum-resilience-built-in/
4. Dell Technologies. *BSAFE Crypto Module Quantum-Resistant Plugin 3.0 release advisory.* https://www.dell.com/support/kbdoc/de-de/000229395/dell-bsafe-crypto-module-quantum-resistant-plugin-3-0-release-advisory?lang=en
5. ITIF (2024). *China is challenging US leadership in quantum technologies.* https://itif.org/publications/2024/09/09/china-is-challenging-us-leadership-in-quantum-technologies-new-report-finds
6. Zaino, J. (26 June 2025). *MIT report describes quantum opportunities, challenges.* MIT Initiative on the Digital Economy, on the *MIT Quantum Index Report 2025*. https://ide.mit.edu/insights/mit-report-describes-quantum-opportunities-challenges/
7. Swarajya (18 April 2023). *Dell CEO wants to reduce supply chain dependence on China.* https://swarajyamag.com/business/dell-ceo-wants-to-reduce-supply-chain-dependence-on-china
8. Foley & Lardner (29 October 2025). *Pivotal push from lab to leverage.* https://www.foley.com/insights/publications/2025/10/pivotal-push-from-lab-to-leverage-why-now-is-the-window-to-secure-foundational-quantum-patents/
9. McKinsey (2025). *Quantum Technology Monitor 2025.* https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/the-year-of-quantum-from-concept-to-reality-in-2025
10. McKinsey. *Five lessons from AI on closing quantum's talent gap.* https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/five-lessons-from-ai-on-closing-quantums-talent-gap-before-its-too-late
11. Decent Cybersecurity (25 July 2025). *Quantum computing's societal impact.* https://decentcybersecurity.eu/quantum-computing-societal-impact/
12. Google Quantum AI (2024). *Quantum error correction below the surface code threshold.* *Nature* **[add DOI]**
13. Dell Technologies (16 March 2026). *Dell breaks the latency barrier in quantum computing with NVIDIA.* https://www.dell.com/en-us/blog/dell-and-nvidia-breaking-the-latency-barrier-in-quantum-computingthe-latency-barrier-in-quantum-computing-with-nvidia/
