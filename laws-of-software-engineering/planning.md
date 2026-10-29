# Laws of Software Engineering — Planning

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **6** principles categorized under **Planning**.

## Table of Contents

- [Premature Optimization (Knuth's Optimization Principle)](#premature-optimization) — *Premature optimization is the root of all evil.* (Junior)
- [Parkinson's Law](#parkinsons-law) — *Work expands to fill the time available for its completion.* (Junior)
- [The Ninety-Ninety Rule](#ninety-ninety-rule) — *The first 90% of the code accounts for the first 90% of development time; the remaining 10% accounts for the other 90%.* (Mid)
- [Hofstadter's Law](#hofstadters-law) — *It always takes longer than you expect, even when you take into account Hofstadter's Law.* (Junior)
- [Goodhart's Law](#goodharts-law) — *When a measure becomes a target, it ceases to be a good measure.* (Senior)
- [Gilb's Law](#gilbs-law) — *Anything you need to quantify can be measured in some way better than not measuring it.* (Mid)

---

<a id="premature-optimization"></a>
## Premature Optimization (Knuth's Optimization Principle)

> **Category:** Planning | **Level:** Junior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/premature-optimization/](https://lawsofsoftwareengineering.com/laws/premature-optimization/)

**Premature optimization is the root of all evil.**

### Key Takeaways

- Most code doesn’t run in performance-critical hotspots, so obsessing over micro-optimizations everywhere wastes time and makes code harder to read and maintain.
- According to Knuth, we should forget about small efficiencies about 97% of the time, and focus on clean design and correct functionality.
- Optimized code is often more complex or less readable. If done prematurely, you incur this cost even when it’s unnecessary.
- Get it working correctly first, then make it fast, then make it pretty.

### Overview

Knuth’s Optimization Principle captures a fundamental trade-off in software engineering: performance improvements often increase complexity. Applying that trade-off before understanding where performance actually matters leads to unreadable systems.

Early in development, your focus should be on a clear design. If you optimize too soon, you might introduce bugs or inflexibility, all to speed up parts of the code that may not even be bottlenecks. It’s often cited that 20% of the code may consume 80% of the execution time (a Pareto-like notion). Optimizing anything outside that critical 20% is wasted effort and adds risk. The principle advises writing simple code, then profiling and improving only the parts that truly need it.

### Examples

A developer writes a low-level C routine with complex bit-twiddling to squeeze out speed, spending two days on it, only to find that the function is called once at startup, taking 0.001% of runtime. The effort was wasted, and the code is now more complex to understand. Meanwhile, another part of the program (such as a sorting function on a large dataset) was the real bottleneck, but remained unoptimized because time was spent on the wrong thing.

Another example is prematurely choosing a complex data structure for theoretical efficiency (say, a custom tree for log(N) lookups) when the simpler approach (like a linear search) would have been acceptable for the data sizes involved.

In contrast, following Knuth’s advice, you implement simply, measure, then find that 80% of time is spent in one loop, you optimize that loop or use a better algorithm there. This gives real improvements with minimal added complexity elsewhere.

### Origins

Donald Knuth, a legendary computer scientist, made this statement in his 1974 paper “Structured Programming with Go To Statements” published in ACM Computing Surveys.

The full quote provides important context: “We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. Yet we should not pass up our opportunities in that critical 3%.”

He didn’t literally mean all evil, but the quote caught on because it resonates with developers who have seen codebases twisted by needless optimizations.

Over time, this quote became almost a proverb in software engineering. It’s taught to juniors: first make it work, then make it right, then (if needed) make it fast.

### Further Reading

- [Structured Programming with go to Statements](https://pic.plover.com/knuth-GOTO.pdf) — Donald Knuth's original 1974 paper in Computing Surveys
- [Code Complete](https://amzn.to/4b6YVBx) — Steve McConnell's comprehensive guide to software construction
- [Program Optimization - Wikipedia](https://en.wikipedia.org/wiki/Program_optimization) — Overview of optimization techniques and when to apply them

### Related Laws

- [YAGNI (You Aren't Gonna Need It)](design.md#yagni)
- [Hofstadter's Law](#hofstadters-law)
- [Gall's Law](architecture.md#galls-law)
- [Kernighan's Law](quality.md#kernighans-law)
- [Amdahl's Law](scale.md#amdahls-law)

---

<a id="parkinsons-law"></a>
## Parkinson's Law

> **Category:** Planning | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/parkinsons-law/](https://lawsofsoftwareengineering.com/laws/parkinsons-law/)

**Work expands to fill the time available for its completion.**

### Key Takeaways

- If you give a task an overly long timeline, people tend to use all of it (or procrastinate until the last minute), so the task takes as long as the deadline allows.
- Giving more time, teams often do polishing (gold-plating) or add minor improvements that aren’t strictly necessary, just to use the whole time allotted for the task.
- A bit stronger (but realistic) deadlines can counteract Parkinson’s Law by having a sense of urgency (called deadline-driven development).

### Overview

This law shows a common problem with time management among developers. If a developer is given two weeks to complete a task that could be done in two days, the work will usually slow down, consuming most of that time. People might spend more time planning, bikeshedding minor details, or simply delaying the start of the work with the understanding that they have enough time.

Parkinson’s Law is often used to warn that loose deadlines reduce productivity, so teams should set clear, realistic time limits. However, managers must use it judiciously, combining Parkinson’s insight with realistic scheduling. If you compress timelines too much, you risk running into Hofstadter’s Law, which reminds us that work often still takes longer than expected, even with buffers.

### Examples

A developer should write a module and is told, “Take as long as you need, maybe a month or two.” In many cases, the developer will not rush to finish it, perhaps experimenting with multiple implementations or polishing noncritical items. The same task, if given a one-week deadline, might have been completed in a week.

Agile teams sometimes apply Parkinson’s Law by **time-boxing tasks**. The fixed, short time box encourages everyone to focus on completing tasks before the sprint ends.

Similarly, if a meeting is scheduled to last all day, it often will. If the same activity were given a two-hour window, participants would likely focus and complete it within that time.

### Origins

Parkinson’s Law was first described in an essay by Cyril Parkinson, published in The Economist in 1955, which initially described how bureaucracies expand over time. The phrase has since entered the lexicon of project management.

It’s not specific to software, but software teams often see it in action during projects.

### Further Reading

- [Parkinson's Law (Original Essay)](https://www.economist.com/news/1955/11/19/parkinsons-law) — Cyril Parkinson's original 1955 essay in The Economist
- [Parkinson's Law: The Book](https://amzn.to/4jg0OOD) — The expanded book version of Parkinson's observations on bureaucracy and time
- [Parkinson's Law - Wikipedia](https://en.wikipedia.org/wiki/Parkinson%27s_law) — Overview of Parkinson's Law and its applications in management

### Related Laws

- [Hofstadter's Law](#hofstadters-law)
- [Brooks's Law](teams.md#brooks-law)

---

<a id="ninety-ninety-rule"></a>
## The Ninety-Ninety Rule

> **Category:** Planning | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/ninety-ninety-rule/](https://lawsofsoftwareengineering.com/laws/ninety-ninety-rule/)

**The first 90% of the code accounts for the first 90% of development time; the remaining 10% accounts for the other 90%.**

### Key Takeaways

- The final parts of a project (polishing, edge cases, integration, bug fixes) often take far more effort than anticipated, often as much as the initial development.
- What looks like the ‘finishing touches’ involves many tricky problems and unknowns.
- Reaching a ‘mostly done’ state can create optimism, but the rule warns that ‘almost done’ often means only halfway in terms of time.

### Overview

This rule quantifies the extent to which projects get stuck in the final phase. Often, teams make good progress at the start, building core functionality, which leads to optimism. Then integration, corner cases, performance tuning, and bug fixing consume an unexpectedly large amount of time, often equal to or greater than what has already been spent.

In practical terms, this rule advises that the last bit of a project is not a small bit. You should plan for a significant effort in finishing, polishing, and delivering.

It is also related to Hofstadter’s Law, as it is another way our estimates fall short. We do not realize how hard that last leg is.

### Examples

A team develops a new app. In three months, the core features are done, and they hit “90% of the functionality.” Everyone expects to ship in one more month. Instead, integration testing reveals that multiple modules do not talk correctly, specific edge inputs crash the app, memory usage is too high. That final “10%” takes another three months.

When implementing a new website, you get a basic version up quickly (login, basic pages). The last bits: cross-browser fixes, responsive design adjustments, accessibility improvements, writing tests, and performance improvements seem like 10% of the work, but they take as much time as the main coding.

The rule is an important reminder: **Do not celebrate too early!**

### Origins

Credited to Tom Cargill of Bell Labs, and popularized by Jon Bentley’s September 1985 “Bumper-Sticker Computer Science” column in Communications of the ACM. It was originally called the “Rule of Credibility”, a name which did not stick.

It became popular in programming circles and is frequently referenced in discussions of why software is usually delivered late or why “90% done” claims can be misleading.

### Further Reading

- [Programming Pearls - Bumper Sticker Computer Science](https://moss.cs.iit.edu/cs100/Bentley_BumperSticker.pdf) — Jon Bentley's original column where the rule was popularized
- [Programming Pearls (Book)](https://amzn.to/49bLHkn) — Jon Bentley's classic book on programming wisdom and techniques
- [Ninety-Ninety Rule - Wikipedia](https://en.wikipedia.org/wiki/Ninety%E2%80%93ninety_rule) — Overview of the rule and its origins at Bell Labs
- [Identifying and Mitigating the Ninety-Ninety Rule in Software Development](https://dev.to/ben/identifying-and-mitigating-the-ninety-ninety-rule-in-software-development-4ap3) — Practical strategies for recognizing and countering the ninety-ninety trap

### Related Laws

- [Hofstadter's Law](#hofstadters-law)
- [Parkinson's Law](#parkinsons-law)
- [Pareto Principle (80/20 Rule)](decisions.md#pareto-principle)

---

<a id="hofstadters-law"></a>
## Hofstadter's Law

> **Category:** Planning | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/hofstadters-law/](https://lawsofsoftwareengineering.com/laws/hofstadters-law/)

**It always takes longer than you expect, even when you take into account Hofstadter's Law.**

### Key Takeaways

- Humans are generally bad at estimating how long tasks take, especially in complex projects. Even when we know we’re bad at it, we still underestimate.
- There are always unknowns and complexities that reveal themselves during implementation, extending the timeline.
- Include contingency buffers in schedules, but even those buffers often get consumed.
- Don’t be overly optimistic in planning. Acknowledge that delays happen and factor that into timelines and expectations.

### Overview

This recursive law captures the paradox of estimation. No matter how much experience we have, projects tend to run late. Even if you say, “This might take 2x longer than I think,” it might still take 3x. It highlights the inherent uncertainty in complex creative work, such as software development. There are often hidden tasks, unplanned integration issues, or requirement changes.

In practice, Hofstadter’s Law explains why techniques like padding estimates, awareness of Parkinson’s Law, and the use of historical data are essential, yet surprises still occur.

It pairs with Parkinson’s Law as a caution: don’t pad too much (Parkinson will waste time), but also don’t be naive (Hofstadter will bite you with delays).

### Examples

Virtually every software project can serve as an example. A team plans a new feature expecting it to take one month. They factor in potential delays and say six weeks to be safe. It ends up taking three months, sometimes even six months later. Why? Integrating with an API was harder, a key developer got sick, or the first approach failed and had to be redone. **The unexpected became the norm**.

A practical rule of thumb: if it takes 2 minutes, do it now. If it takes a few minutes, call it 1 hour. If it takes a few hours, call it 1 day. We are not working to prove speed, but to buy enough space to ship well.

### Origins

Douglas Hofstadter created this law in 1979 in his book “Gödel, Escher, Bach: An Eternal Golden Braid”. The book explores themes of recursion and self-reference, making this recursive law a fitting example.

In software engineering, Fred Brooks’ observation “everything takes longer than it takes” from The Mythical Man-Month has a similar meaning. The law has become common among developers who’ve all experienced projects that overshoot schedules.

### Further Reading

- [Gödel, Escher, Bach: An Eternal Golden Braid](https://amzn.to/4jjKSLl) — Douglas Hofstadter's Pulitzer Prize-winning book where the law first appeared
- [The Mythical Man-Month](https://amzn.to/49cAqQO) — Fred Brooks' classic on software project management with similar insights on estimation
- [Why Software Projects Take Longer Than You Think](https://erikbern.com/2019/04/15/why-software-projects-take-longer-than-you-think-a-statistical-model.html) — A statistical model explaining estimation failures

### Related Laws

- [Parkinson's Law](#parkinsons-law)

---

<a id="goodharts-law"></a>
## Goodhart's Law

> **Category:** Planning | **Level:** Senior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/goodharts-law/](https://lawsofsoftwareengineering.com/laws/goodharts-law/)

**When a measure becomes a target, it ceases to be a good measure.**

### Key Takeaways

- If you set a particular metric as a goal (e.g., lines of code written, number of features closed), people will find ways to optimize for that metric.
- Metrics are proxies for what you value (productivity, quality, etc.). Once they’re targets, people meet the metric even if it undermines the original intent.
- Metrics are useful for insight, but they must be used in context and balanced with qualitative judgment.
- Combine multiple metrics to avoid a singular focus that can be gamed.

### Overview

Goodhart’s Law comes from economics and is very relevant to software teams. For instance, a manager might set a target that “we must close 100 bug tickets this month.” Developers, feeling pressure, might start closing tickets that are not truly resolved or splitting a single bug into multiple tickets to inflate numbers.

The metric (tickets closed) goes up, but software quality might not. Making the metric a goal distorts the process, so it loses its correlation with actual success. This is why experienced leaders use metrics as indicators rather than targets, and always consider the broader context.

### Examples

A software team was rewarded based on the lines of code written. Developers start writing verbose code and copying and pasting into multiple places (violating DRY) to increase the line count. The software becomes bloated while the metric looks great.

Another example: a QA team measured by the number of test cases executed favored running many easy tests rather than doing proper testing. They met objectives but missed critical bugs.

Similarly, when teams focus on **code coverage percentage** as a primary target, developers write trivial unit tests that do not assert meaningful behavior, while necessary integration tests are skipped.

A recent variant is measuring AI tokens consumed per engineer (a practice sometimes called **tokenmaxxing**), where more tokens are considered better and token counts even become goals that people need to fulfill for their performance reviews.

### Origins

Named after economist Charles Goodhart, who originally described this phenomenon in the context of monetary policy metrics. Marilyn Strathern later provided the commonly cited phrasing: “When a measure becomes a target, it ceases to be a good measure.”

This concept has been discussed extensively in education and business KPIs, and certainly applies to software engineering metrics where velocity, code coverage, and bug counts are often used as targets.

### Further Reading

- [Goodhart's Law: How Measuring The Wrong Things Drive Immoral Behaviour](https://coffeeandjunk.com/goodharts-campbells-law/) — Deep dive into Goodhart's Law and its implications for organizations
- [Goodhart's Law - Wikipedia](https://en.wikipedia.org/wiki/Goodhart%27s_law) — Overview of the law's origins and applications
- [The Tyranny of Metrics](https://amzn.to/4ji7rzY) — Jerry Muller's book on the unintended consequences of metric fixation
- [Enshittification - Wikipedia](https://en.wikipedia.org/wiki/Enshittification) — How platforms degrade quality once metrics replace user value as the goal

### Related Laws

- [Dilbert Principle](teams.md#dilbert-principle)
- [Parkinson's Law](#parkinsons-law)

---

<a id="gilbs-law"></a>
## Gilb's Law

> **Category:** Planning | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/gilbs-law/](https://lawsofsoftwareengineering.com/laws/gilbs-law/)

**Anything you need to quantify can be measured in some way better than not measuring it.**

### Key Takeaways

- It is better to have some data or metric on a phenomenon than to be completely blind, as long as you understand the metric’s limitations.
- In contrast to Goodhart’s Law, which warns about misuse of metrics, Gilb’s Law reminds us not to throw out metrics entirely.
- Start with a basic measure and refine it over time. The act of measuring helps teams focus and identify trends.
- Even an approximate or indirect measurement is better than none.

### Overview

Gilb’s Law responds to the paralysis that Goodhart’s Law can cause. This law asserts that even an approximate or indirect measurement is better than none. When something is essential (performance, customer satisfaction, code maintainability), you should attempt to measure it, because otherwise you have no objective feedback.

Gilb’s Law is a good reply to the statement “this aspect is unmeasurable so we won’t try.” For example, measuring “code quality” is difficult, but you can measure indicators such as cyclomatic complexity, lint warnings, or defect rates as partial indicators. More such indicators can paint the bigger picture.

Those metrics won’t be perfect, but Gilb’s Law suggests that having them gives you some insight and a starting point for improvement, which is better than having no clue at all.

### Examples

Measuring **developer productivity** is notoriously hard (lines of code are poor proxies, story points can be inconsistent). However, you might use deployment frequency or change lead time (as in the DORA metrics for DevOps) as a proxy. They do not capture everything, but they give you actionable data. If deployment frequency decreases, something might be wrong with the pipeline.

Another example is **tracking Tech Debt**. No perfect measure of tech debt exists. But tracking things like code complexity scores, incident rates, and developer surveys gives you visibility you would not otherwise have. As Peter Drucker said: “We cannot improve what we do not measure.”

### Further Reading

- [Tom Gilb - Wikipedia](https://en.wikipedia.org/wiki/Tom_Gilb) — Overview of Tom Gilb's contributions to software engineering
- [Competitive Engineering](https://amzn.to/49AqaT1) — Tom Gilb's book on quantified requirements and design
- [DORA Metrics](https://dora.dev/guides/dora-metrics-four-keys/) — The four key metrics for measuring DevOps performance

### Related Laws

- [Goodhart's Law](#goodharts-law)
- [Parkinson's Law](#parkinsons-law)

---
