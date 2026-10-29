# Laws of Software Engineering — Quality

Extracted from [Laws of Software Engineering](https://lawsofsoftwareengineering.com/). This document covers all **11** principles categorized under **Quality**.

## Table of Contents

- [The Boy Scout Rule](#boy-scout-rule) — *Leave the code better than you found it.* (Junior)
- [Murphy's Law / Sod's Law](#murphys-law) — *Anything that can go wrong will go wrong.* (Junior)
- [Postel's Law](#postels-law) — *Be conservative in what you do, be liberal in what you accept from others.* (Mid)
- [Broken Windows Theory](#broken-windows-theory) — *Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.* (Mid)
- [Technical Debt](#technical-debt) — *Technical Debt is everything that slows us down when developing software.* (Junior)
- [Linus's Law](#linuss-law) — *Given enough eyeballs, all bugs are shallow.* (Mid)
- [Kernighan's Law](#kernighans-law) — *Debugging is twice as hard as writing the code in the first place.* (Junior)
- [Testing Pyramid](#testing-pyramid) — *A project should have many fast unit tests, fewer integration tests, and only a small number of UI tests.* (Junior)
- [Pesticide Paradox](#pesticide-paradox) — *Repeatedly running the same tests becomes less effective over time.* (Mid)
- [Lehman's Laws of Software Evolution](#lehmans-laws) — *Software that reflects the real world must evolve, and that evolution has predictable limits.* (Senior)
- [Sturgeon's Law](#sturgeons-law) — *90% of everything is crap.* (Junior)

---

<a id="boy-scout-rule"></a>
## The Boy Scout Rule

> **Category:** Quality | **Level:** Junior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/boy-scout-rule/](https://lawsofsoftwareengineering.com/laws/boy-scout-rule/)

**Leave the code better than you found it.**

### Key Takeaways

- Don’t leave bad things rot in a project. This means take a moment to refactor or fix at least one small thing in the area you’re working on. It can include anything from variable names to simplifying logic.
- A cleaner codebase is easier to read, work with, and extend. This improves project maintainability and reduces technical debt.
- When every developer follows this rule, it creates a culture of ownership in the code. Teams collectively feel responsible for code quality.

### Overview

The Boy Scout Rule basically means: leave the code better than you found it. In practice, it’s not about doing big-bang rewrites or achieving perfection in one go. Instead, it’s about constant and incremental improvements.

Whenever a developer encounters a piece of code, whether adding a new feature or hunting down a bug, they take the opportunity to polish something nearby. For example, if there’s a confusing function name, you rename it clearly. If you notice some duplicated code, you refactor it into a single helper. If a test case is missing for a critical method, you add it.

These are often small changes that might take only a few extra minutes, but they compound over time.

### Examples

You’re working on an old module to add a new feature. The code works, but you notice a couple of things: there’s a function `processData()` that has more than 200 lines, and there are some `//TODO` comments and commented-out code blocks. Following the rule, you split `processData()` into smaller, better-named functions to improve readability and delete those commented-out sections that are no longer needed.

On a larger scale, Google’s engineers often say “If you touch it, you own it”. This means that when you modify code, you take ownership of its quality, leading to fixing even minor issues as they arise during unrelated tasks. Over the lifespan of a product, thousands of such small clean-ups occur, preventing major problems.

### Origins

The mantra “leave the campsite cleaner than you found it” comes from the Boy Scouts of America and Scouting organizations worldwide.

In the domain of software development, the Boy Scout Rule was popularized by Robert C. Martin (Uncle Bob) in his book “Clean Code: A Handbook of Agile Software Craftsmanship” (2008).

Uncle Bob adapted this simple wisdom to software development, recognizing that large refactoring projects rarely happen but continuous small improvements can transform a codebase over time.

### Further Reading

- [Clean Code: A Handbook of Agile Software Craftsmanship](https://amzn.to/3LjRFYI) — Robert C. Martin's influential book on writing clean code
- [The Boy Scout Rule](https://www.oreilly.com/library/view/97-things-every/9780596809515/ch08.html) — Uncle Bob's essay in 97 Things Every Programmer Should Know
- [Refactoring: Improving the Design of Existing Code](https://martinfowler.com/books/refactoring.html) — Martin Fowler's guide to incremental code improvement
- [Code Complete](https://amzn.to/3N57T8t) — Steve McConnell's comprehensive guide to software construction

### Related Laws

- [Broken Windows Theory](#broken-windows-theory)
- [YAGNI (You Aren't Gonna Need It)](design.md#yagni)
- [Technical Debt](#technical-debt)

---

<a id="murphys-law"></a>
## Murphy's Law / Sod's Law

> **Category:** Quality | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/murphys-law/](https://lawsofsoftwareengineering.com/laws/murphys-law/)

**Anything that can go wrong will go wrong.**

### Key Takeaways

- If an error can happen, it will happen. Plan and code defensively with this in mind.
- Add error handling, backups, and checks.
- Edge cases will occur in production. Write tests for these kinds of scenarios.

### Overview

In software, Murphy’s Law is often used to explain bugs and production incidents: whatever can go wrong in code (a null pointer, a race condition, a network outage) eventually will manifest, especially in large user bases or at the worst possible time.

In practice, this law encourages developers to write more defensive code. This means checking for nulls, handling exceptions, validating inputs, and failing gracefully when errors occur. It also reminds DevOps teams to anticipate failures by implementing monitoring, enabling rollbacks, and maintaining contingency plans.

### Examples

If a web form field can accept text, someone will enter a 10,000-character string of weird symbols to see what happens, unless you’ve explicitly handled it. If memory can run out, it will be when multiple processes align just so.

A famous real-world instance was during a live demo (who remembers the Windows 98 presentation by Bill Gates?), if something can glitch, it likely will.

In coding, consider a function that assumes an input file exists. Murphy’s Law says that one day that file won’t be there or will be corrupted, so your code should handle the file-not-found or bad-data scenario rather than crash.

Another typical case is that the server will crash on your only day off, because that’s when it’s most likely to cause trouble. Engineers thus build highly available systems and pager rotations to mitigate Murphy’s Law.

### Further Reading

- [Murphy's Law - Wikipedia](https://en.wikipedia.org/wiki/Murphy%27s_law) — History and variations of the famous adage
- [Windows 98 Crash During Live Demo](https://www.youtube.com/watch?v=yeUyxjLhAxU) — Bill Gates' infamous BSOD during a Windows 98 presentation
- [Defensive Programming](https://en.wikipedia.org/wiki/Defensive_programming) — Programming practices to anticipate and handle errors
- [CrowdStrike Channel File 291 RCA Exec Summary](https://www.crowdstrike.com/falcon-content-update-remediation-and-guidance-hub/) — Root cause analysis of the CrowdStrike outage, a real-world example of Murphy's Law at scale

### Related Laws

- [Confirmation Bias](decisions.md#confirmation-bias)

---

<a id="postels-law"></a>
## Postel's Law

> **Category:** Quality | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/postels-law/](https://lawsofsoftwareengineering.com/laws/postels-law/)

**Be conservative in what you do, be liberal in what you accept from others.**

### Key Takeaways

- When your system emits data or interacts with the outside world, adhere closely to protocols and standards.
- When receiving data, handle variations, minor errors, or deviations where possible. Don’t crash or reject communication over minor issues.
- In modern times, overly liberal acceptance can sometimes mask errors, so this law is occasionally tempered with security considerations.

### Overview

This law says that if your server sends HTTP responses, it should format headers exactly per spec. But if your server receives an HTTP request with an uncommon header order or an unusual format, you should still process it rather than drop the connection, as long as you can interpret it safely.

This principle contributed to the Internet’s resilience, meaning that different implementations can communicate because each side strives to be compatible.

In software in general, think of file readers: a robust one can open not-quite-perfect files (e.g., a tolerant XML parser might recover from a minor error), whereas a strict one might refuse. Postel’s Law would encourage the former. However, it has caveats. Being too liberal can allow sloppy producers to proliferate, and in security contexts, accepting malformed input can be risky. Some argue that overly tolerant software can cause long-term interoperability problems because producers never fix their bugs if everyone tolerates them.

### Examples

In **web browsers**, HTML on websites is often malformed. Browsers, following Postel’s spirit, perform extensive error correction and forgiving parsing. They’ll still render the page even if a tag isn’t closed correctly. If browsers were strict, half the web pages might not display.

In **APIs**, say your service expects a timestamp. If it receives a timestamp without a time zone, instead of rejecting, maybe you assume UTC or try to parse it anyway, being liberal in acceptance. But when your service returns data, you always include the time zone to be conservative and precise in output.

An **email client** that receives a slightly non-conforming email (missing a MIME boundary or incorrect newline encodings) will still attempt to show the email rather than throwing an error.

### Origins

Jon Postel wrote this in the specification of TCP in 1980 (RFC 761): “TCP implementations should follow a general principle of robustness: be conservative in what you send, be liberal in what you accept.” It became known as Postel’s Law or the Robustness Principle and influenced many protocol designs.

There’s a modern reconsideration: the HTML5 spec codified much of the error handling that browsers already do, arguing that all that “liberal acceptance” should itself be standardized to avoid ambiguity.

### Further Reading

- [Robustness Principle - Wikipedia](https://en.wikipedia.org/wiki/Robustness_principle) — Overview of Postel's Law and its applications
- [RFC 761 - DoD Standard Transmission Control Protocol](https://datatracker.ietf.org/doc/html/rfc761) — The TCP specification where Postel articulated the robustness principle
- [The Harmful Consequences of Postel's Maxim](https://datatracker.ietf.org/doc/html/draft-thomson-postel-was-wrong-00) — A critical examination of when being too liberal causes problems
- [The Robustness Principle Reconsidered](https://queue.acm.org/detail.cfm?id=1999945) — Eric Allman's ACM Queue article on security implications of liberal acceptance

### Related Laws

- [Hyrum's Law](architecture.md#hyrums-law)
- [The Law of Leaky Abstractions](architecture.md#law-of-leaky-abstractions)
- [Fallacies of Distributed Computing](architecture.md#fallacies-of-distributed-computing)

---

<a id="broken-windows-theory"></a>
## Broken Windows Theory

> **Category:** Quality | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/broken-windows-theory/](https://lawsofsoftwareengineering.com/laws/broken-windows-theory/)

**Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.**

### Key Takeaways

- If you let minor bugs and bad style slide, people assume quality doesn’t matter, and they’ll ship messier code.
- A clean, well-maintained codebase encourages engineers to keep it clean, whereas a chaotic codebase encourages corner-cutting and further degradation.
- Fix problems while they’re small. Refactor destructive code, update outdated docs, to prevent a downward spiral of code health.

### Overview

The Broken Windows Theory in software was popularized by the book The Pragmatic Programmer. In a city, a broken window left unfixed signals neglect and invites more vandalism. Similarly in code, an apparent bug or messy section left untreated can lead to more developers bypassing the process or introducing more mess.

The idea is that quality problems snowball if left unaddressed. For example, if a team routinely ignores failing tests or lets linters/errors slide during builds, developers get the message that it’s okay to ship sloppy work. This accelerates code decay (also known as software entropy).

Conversely, if a team quickly fixes minor issues and maintains high standards, it creates a culture of quality.

### Examples

Consider a codebase with a few obvious kludges, such as functions with `// TODO: fix this hack` comments that never get fixed. If newcomers see that, they may be more inclined to add their own hacks (“this project is full of hacks anyway…”). Or if there’s a module with no tests (a “broken window” in a test-coverage sense), other modules might start losing tests too as discipline erodes.

On the opposite side, think of a project where maintainers aggressively fix style issues and simplify code whenever they spot a problem. By contributing to such a project, developers quickly learn to match that cleanliness.

Many teams have turned projects around by paying off technical debt and cleaning up code. Once things are polished, they find fewer new bugs are introduced because everyone is more careful.

### Origins

The Broken Windows Theory comes from criminology (James Q. Wilson and George Kelling, 1982). In software, Andy Hunt and Dave Thomas applied it as a metaphor in The Pragmatic Programmer (1999). They argued for fixing minor problems promptly.

Jeff Atwood and others in blogs have also discussed this principle in the context of software project maintenance.

### Further Reading

- [The Broken Window Theory - Coding Horror](https://blog.codinghorror.com/the-broken-window-theory/) — Jeff Atwood's discussion of applying this theory to software
- [Broken Windows Theory - Wikipedia](https://en.wikipedia.org/wiki/Broken_windows_theory) — The original criminological theory
- [The Pragmatic Programmer](https://amzn.to/4qygIq6) — The book that popularized this concept in software engineering
- [Joy of Programming: The Broken Window Theory](https://opensourceforu.com/2011/05/joy-of-programming-broken-window-theory/) — Practical application of the theory in software development

### Related Laws

- [Technical Debt](#technical-debt)
- [The Boy Scout Rule](#boy-scout-rule)
- [Gall's Law](architecture.md#galls-law)

---

<a id="technical-debt"></a>
## Technical Debt

> **Category:** Quality | **Level:** Junior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/technical-debt/](https://lawsofsoftwareengineering.com/laws/technical-debt/)

**Technical Debt is everything that slows us down when developing software.**

### Key Takeaways

- When we take a shortcut in code, we borrow time from the future. This gives an immediate benefit, but you owe principal (the work to fix) plus interest.
- If technical debt is not repaid, it accrues interest. Each minute spent on dirty code, bugs, and workarounds due to a lack of refactoring is interest on the debt.
- Not all technical debt is inherently bad. It is sometimes necessary, for instance, for market timing or prototyping.
- The way to pay down technical debt is to refactor code, add missing tests, and improve design.

### Overview

Technical debt highlights a fundamental tension in software engineering: speed vs. quality. The term helps explain to both developers and non-technical stakeholders why seemingly “done” software still needs ongoing work. When you write clumsy code or postpone cleanup, you’ve essentially taken out a loan: you get short-term feature delivery, but the complexity you introduce is the interest you’ll keep paying.

Properly managing technical debt means being conscious of when you’re adding a quick workaround or a “temporary” hack, and having a plan to revisit it. Teams often use tools to log technical debt items (like comments, issue tracker tickets, or dedicated debt backlogs).

When managed, technical debt can be an effective tool; you intentionally take on a bit of messiness to get feedback or meet a deadline, then clean it up. But if ignored, debt becomes a problem.

### Examples

A typical example is skipping automated tests. A team under deadline pressure releases a new feature without writing tests. The release is successful (debt incurred). But later, making changes becomes harder since every change risks unforeseen bugs because there’s no safety net of tests (interest payments). Eventually they must stop adding features and fix the debt by adding the missing tests and refactoring.

Another example is a startup that wants to deliver a quick prototyping effort to onboard the first customer. Developers do rapid but messy coding, with hardcoded variables and copy-and-paste code. This approach is made with technical debt in mind. The endeavor helps the startup win a customer; however, the startup’s codebase is now full of technical debt.

If they just continue to add to it, they will face bugs and slower performance due to the messy code (interest on debt). They realize this and therefore set up a “rehab” sprint to refactor the code, thereby resolving the most troublesome bits.

### Origins

The term “Technical Debt” was coined by Ward Cunningham (one of the authors of the Agile Manifesto) at the OOPSLA conference in 1992. He first used the financial metaphor while working on a finance application to explain to his boss why the team needed time to refactor code.

Ward compared developing software to borrowing money: it can be wise to take shortcuts (borrow) to achieve something sooner, provided you pay back the loan by cleaning up the code later.

### Further Reading

- [Debt Metaphor - Ward Cunningham](https://www.youtube.com/watch?v=pqeJFYwnkjE) — Ward Cunningham's video explaining the original debt metaphor (OOPSLA 1992)
- [Technical Debt - Martin Fowler](https://martinfowler.com/bliki/TechnicalDebt.html) — Martin Fowler's comprehensive blog post on technical debt
- [Technical Debt - Wikipedia](https://en.wikipedia.org/wiki/Technical_debt) — Overview of the concept and its management strategies
- [Accelerate](https://amzn.to/48Xugp3) — Forsgren, Humble, and Kim's research on how technical debt impacts software delivery

### Related Laws

- [Broken Windows Theory](#broken-windows-theory)
- [Hofstadter's Law](planning.md#hofstadters-law)
- [The Boy Scout Rule](#boy-scout-rule)

---

<a id="linuss-law"></a>
## Linus's Law

> **Category:** Quality | **Level:** Mid | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/linuss-law/](https://lawsofsoftwareengineering.com/laws/linuss-law/)

**Given enough eyeballs, all bugs are shallow.**

### Key Takeaways

- Linus’s Law highlights the strength of peer review and community in software development. If a codebase is accessible to many developers, someone will eventually have the expertise to identify and fix a given bug.
- The rule is often cited as a key advantage of open-source software. When source code is widely available, you accumulate a large pool of contributors.
- Linus’s Law assumes those eyeballs are indeed looking, i.e., an active community. Simply being open-source doesn’t magically fix bugs.

### Overview

Linux’s open development model, releasing code early and often to the public, results in rapid bug-finding. When many people use and review a piece of software, problems become apparent to someone.

What is a perplexing bug to you might be trivial to another programmer who spots it. Or among thousands of users, one will stumble on the exact reproduction steps, and another might submit a fix.

This law shows the core of open-source: that transparency and collaboration lead to more robust, reliable software.

However, it’s not absolute. Coordination and quality control are still needed. But as a guiding principle, Linus’s Law captures the self-correcting nature of a large developer ecosystem.

The “many eyeballs” principle is also why internal code reviews and pair programming can be effective.

### Examples

Consider the Apache HTTP Server, an open-source web server used by millions. Because its code is open and it has a vast user base, many developers have at some point debugged or improved it. If there’s a security flaw or bug, odds are high that someone in the global community will discover it and report it. The infamous “Log4Shell” vulnerability in the Log4j library was identified and patched by the community.

In contrast, consider an enterprise software product that is proprietary with only a few clients. If a subtle bug appears, only the vendor’s small team and a few client implementers are likely to notice it. It might take a long time to surface and debug because of limited “eyeballs.”

### Origins

The law is named after Linus Torvalds, the creator of Linux, but Eric S. Raymond formulated it in the late 1990s. In “The Cathedral and the Bazaar”, Raymond writes: “Given enough eyeballs, all bugs are shallow” and calls this Linus’s Law in honor of Torvalds’ open development approach.

The idea was inspired by the Linux community, where hundreds of developers worldwide were debugging the kernel simultaneously. The essay was first presented in 1997 and published as a book in 1999.

### Further Reading

- [The Cathedral and the Bazaar](https://amzn.to/49cYD9Y) — Eric S. Raymond's influential essay on open-source development
- [Linus's Law - Wikipedia](https://en.wikipedia.org/wiki/Linus%27s_law) — Overview of the law and its implications
- [With Enough Eyeballs, All Bugs Are Shallow - TechCrunch](https://techcrunch.com/2012/02/23/with-many-eyeballs-all-bugs-are-shallow/) — Analysis of the law in context of real-world vulnerabilities
- [Revisiting Linus's Law: Benefits and Challenges of OSS Peer Review](https://www.sciencedirect.com/science/article/abs/pii/S1071581915000087) — Academic study on the impacts of member differences on open source peer review
- [An Empirical Study of Build Maintenance Effort - IEEE](https://www.computer.org/csdl/magazine/mi/2012/01/mmi2012010072/13rRUzphDuy) — IEEE study examining software maintenance and the many-eyes hypothesis
- [Timeline of the xz open source attack](https://research.swtch.com/xz-timeline) — Russ Cox's detailed timeline of the xz backdoor, a striking counterexample to many-eyes review

### Related Laws

- [Brooks's Law](teams.md#brooks-law)
- [Sturgeon's Law](#sturgeons-law)
- [Bus Factor](teams.md#bus-factor)

---

<a id="kernighans-law"></a>
## Kernighan's Law

> **Category:** Quality | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/kernighans-law/](https://lawsofsoftwareengineering.com/laws/kernighans-law/)

**Debugging is twice as hard as writing the code in the first place.**

### Key Takeaways

- Bug detection and removal is more complex than programming because debugging requires understanding both the code and why it doesn’t work.
- If you write code at the limit of your intelligence, you won’t be able to understand or troubleshoot it later.
- Simple code with good structure and documentation is easier to debug, saving time in the long run.
- Even if your code runs successfully when you write it, it’s fragile if it’s too complex.

### Overview

Kernighan’s Law says that debugging requires understanding what the code *actually* does, which can be twice as hard as writing it. When coding, you operate with a specific mental model and full context. When debugging, you might be dealing with someone else’s code or your own code after that context has faded.

Writing “clever” or complex code is essentially setting a trap for your future self. A maintainable version is usually superior to an optimized version that is difficult to understand. As Kernighan implies, if you make your code too tricky, you’ve essentially outsmarted yourself.

### Examples

Imagine a developer writing a function in a compressed style, chaining multiple operations in one line:

The proper, readable version:

The clever version might have taken 30 minutes to write, but debugging took 3 hours. Had the code been written clearly, it would’ve taken 45 minutes to write, but only 30 minutes to debug later.

### Further Reading

- [The C Programming Language](https://amzn.to/3YLSFYy) — The classic 'K&R' book co-authored by Brian Kernighan
- [The Elements of Programming Style](https://www.amazon.com/Elements-Programming-Style-2nd/dp/0070342075) — Kernighan and Plauger's guide to writing clear code
- [Code Complete](https://amzn.to/4smkSmE) — Steve McConnell's comprehensive guide to software construction

### Related Laws

- [KISS (Keep It Simple, Stupid)](design.md#kiss-principle)
- [Premature Optimization (Knuth's Optimization Principle)](planning.md#premature-optimization)

---

<a id="testing-pyramid"></a>
## Testing Pyramid

> **Category:** Quality | **Level:** Junior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/testing-pyramid/](https://lawsofsoftwareengineering.com/laws/testing-pyramid/)

**A project should have many fast unit tests, fewer integration tests, and only a small number of UI tests.**

### Key Takeaways

- Unit testing is where you start. Unit tests are run as separate functions and execute quickly. That means you can afford to write lots of unit tests.
- After the unit tests, there must be an integration test layer. These verify the integration of modules. You will require fewer integration tests than unit tests.
- End-to-end tests at the top simulate real-world user scenarios. They are essential but slow and expensive to maintain.
- Organizing tests this way, you receive quick feedback (most tests are quick unit tests), and when your UI test fails, there’s a better chance it’s due to a real problem.

### Overview

The pyramid is a visual metaphor: the largest level (at the bottom) is unit tests, which are fast and the most numerous. The middle layer is integration tests, fewer in number. The top is UI/end-to-end tests, the least numerous. As you go up, tests become more expensive in time, effort, and fragility, so you want proportionally fewer of them.

By following the pyramid, most bugs are caught at the cheapest level. If the pyramid is inverted (lots of end-to-end tests, few unit tests), the test suite tends to be slow and fragile.

### Examples

Consider a web e-commerce application. Following the test pyramid, the team writes extensive unit tests for functions such as price calculation, discount logic, and validation (hundreds of unit tests). They also write API integration tests verifying that order placement connects inventory, payment, and notification services correctly (a few dozen tests). Finally, they have a few end-to-end tests simulating user journeys like browsing, adding to cart, and checkout.

Because they have so many unit tests, if something in business logic breaks, it’s caught before end-to-end tests run. This approach takes little time in CI and allows confident deployments.

Now consider a team that did not follow the pyramid. They have few unit tests and instead rely on 50 end-to-end GUI tests that run nightly for hours. They often find failing tests, but it’s hard to tell if it’s genuine bugs or test flakiness. Developers get feedback with a day’s delay. This is the *anti-pattern* the pyramid warns against.

### Origins

Mike Cohn is credited with popularizing the Test Pyramid. He described it in his book *Succeeding with Agile* and blog posts around 2009, coining the term and concept.

The idea builds on earlier testing theory (such as test levels in the ISTQB foundation or the general practice in TDD of writing many unit tests). Modern discussions sometimes add layers or modify terms, but the core principle remains: **test more at the unit level than at the UI level**.

### Further Reading

- [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) — Martin Fowler's comprehensive guide to the test pyramid
- [Succeeding with Agile](https://amzn.to/4pb7Q8v) — Mike Cohn's book where the Test Pyramid was popularized
- [Test Pyramid - Wikipedia](https://en.wikipedia.org/wiki/Test_automation#Testing_at_different_levels) — Overview of test automation at different levels
- [Software Engineering at Google, Chapter 11: Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) — Titus Winters, Tom Manshreck & Hyrum Wright on Google's testing philosophy and practices

### Related Laws

- [Lehman's Laws of Software Evolution](#lehmans-laws)

---

<a id="pesticide-paradox"></a>
## Pesticide Paradox

> **Category:** Quality | **Level:** Mid | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/pesticide-paradox/](https://lawsofsoftwareengineering.com/laws/pesticide-paradox/)

**Repeatedly running the same tests becomes less effective over time.**

### Key Takeaways

- Over time, an outdated test suite will identify fewer bugs. The tests are still helpful, but no longer effective at detecting new defects.
- This paradox illustrates the need to infuse new test data continuously. It is essential for testers not to become complacent with their test scripts, thinking that these alone will be sufficient in the future.
- By periodically creating new tests (by altering existing ones), you effectively ‘refresh the pesticide,’ thereby providing an opportunity to catch new bugs. This involves extending tests for new functionality, trying new input combinations, or perhaps just investigating new boundary cases.

### Overview

The “Pesticide Paradox” analogy comes from agriculture. When the same pesticide is used repeatedly, pests develop resistance to it.

In software, the first runs of a new test suite might find many bugs. Those bugs get fixed. If you keep running the same tests without changes, you won’t find more bugs there. The software has become “immune” to those specific tests.

The testing process cannot be stagnant. Test cases must be maintained regularly. After every release cycle, testers should assess which bugs made it to production and enhance the test suite accordingly.

This paradox also argues for exploratory testing, where testers approach the application in new ways each iteration, uncovering problems a static regression suite would miss. The paradox doesn’t mean regression testing is useless, as old tests catch regressions. But to catch *new* bugs, you must design *new* tests.

### Examples

Let’s consider a mobile app where, in the first release, testers wrote extensive tests for the login and user profile features, finding and getting ten bugs fixed in those areas. In the subsequent releases, those test cases all pass (no new bugs in login or profile, great). Meanwhile, the app has added a messaging feature, but the test suite didn’t add many cases for it. However, within a couple of releases, complaints started trickling in regarding the messaging functionality crashing. Unfortunately, the test suite failed to identify these because it was not updated to test messaging, which is predominantly centered on login and profile.

This is the pesticide paradox, which states that as testing became green (no defects remained in the code tested), new defects began to emerge, thereby requiring new tests. However, after the group includes their messaging tests, they begin to uncover these issues before they become releases. This process continues until those tests no longer find new issues, and the pattern repeats with the following features that emerge.

### Origins

The concept was articulated by Dr. Boris Beizer, a software testing expert, and became widely known as one of the “seven principles of testing” in ISTQB (International Software Testing Qualifications Board) materials.

Beizer stated something to the effect of: every method of testing will yield a pesticide paradox, bugs adapt to tests, leaving more subtle bugs behind.

### Further Reading

- [Software Testing Techniques](https://amzn.to/3Yg3jH4) — Boris Beizer's comprehensive book on testing techniques
- [ISTQB Foundation Level Syllabus](https://www.istqb.org/certifications/certified-tester-foundation-level) — Official ISTQB syllabus covering the seven principles of testing
- [Lessons Learned in Software Testing](https://amzn.to/3YNqIzD) — Practical wisdom on software testing by Kaner, Bach, and Pettichord

### Related Laws

- [Lehman's Laws of Software Evolution](#lehmans-laws)
- [Testing Pyramid](#testing-pyramid)

---

<a id="lehmans-laws"></a>
## Lehman's Laws of Software Evolution

> **Category:** Quality | **Level:** Senior | **Read Time:** 3 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/lehmans-laws/](https://lawsofsoftwareengineering.com/laws/lehmans-laws/)

**Software that reflects the real world must evolve, and that evolution has predictable limits.**

### Key Takeaways

- The first law, Continuing Change, states that if a system isn’t continuously updated to meet new needs, it becomes less satisfactory to use. In practice, this means that successful software is never truly ‘finished’; to remain useful, it undergoes ongoing enhancements (or else users abandon it for something that keeps up).
- Over time, changes accumulate, making the system more complex (Law 2). Unless developers invest in refactoring or restructuring (i.e., paying down technical debt), the system’s internal complexity will increase, slowing further development.
- Even if users demand more, a development organization can only do so much in a given time. They can’t exponentially accelerate delivery forever. Factors such as team knowledge (familiarity) and process overhead limit it.
- The perceived quality of the system will decline (perhaps due to rising user expectations, environmental changes, or the accumulation of minor issues).

### Overview

Lehman’s Laws describe an unavoidable reality of long-lived software systems that operate in the real world. Such systems, business software, operating systems, and platforms, must continuously change to remain useful. That change is neither optional nor free.

As software evolves, complexity accumulates. Each change slightly increases internal disorder unless effort is spent counteracting it. Over time, this complexity reduces development speed, increases risk, and raises the cost of further change. Teams feel this as “everything taking longer than it used to.”

Organizations face hard limits: knowledge, coordination, and familiarity constrain how much change can be absorbed in a single release. Adding people does not remove these limits; it often reinforces them.

### Examples

Consider a big **enterprise resource planning (ERP) system** deployed in 2000. Over 25 years, updates included new business rules, integrations with new technologies, and UI refreshes. According to Law 1 (Continuing Change), this was necessary. If they hadn’t continued updating, the system would no longer meet business needs. The company observes that adding functionality in 2025 takes longer than it did in 2005, reflecting Laws 2 and 7. Periodically, cleanup projects (refactoring) were needed, but output per year stabilized (Laws 4 and 5).

The **Linux kernel** provides another example. It has undergone continuous change, adapting to new hardware and requirements. If it stopped adapting, it would become irrelevant. Its functionality has grown massively, and complexity has increased, requiring subsystem maintainers.

The “conservation of familiarity” is seen in how changes are managed: big rewrites are rare, and maintainers enforce a pace the community can keep up with.

### Origins

Lehman’s early laws were formulated in 1974, based on his study of various software, including IBM’s OS/360. Lehman and Belady observed version histories, growth metrics, and other data, leading to the initial three laws.

Over the years, Lehman refined the laws through the 1980s and 1990s as more projects provided data. Initially there were 3 laws (1974), then 5, and eventually 8 laws by the 1990s.

### Further Reading

- [Programs, Life Cycles, and Laws of Software Evolution](https://ieeexplore.ieee.org/document/1456074) — Lehman & Belady's original 1980 paper on software evolution
- [Laws of Software Evolution - The Nineties View](https://ieeexplore.ieee.org/document/637156) — Lehman et al. 1997 update on the laws with additional research
- [The Evolution of the Laws of Software Evolution](https://link.springer.com/chapter/10.1007/978-3-540-75381-0_1) — Overview of how Lehman's Laws evolved over time

### Related Laws

- [Brooks's Law](teams.md#brooks-law)
- [Conway's Law](teams.md#conways-law)
- [Technical Debt](#technical-debt)

---

<a id="sturgeons-law"></a>
## Sturgeon's Law

> **Category:** Quality | **Level:** Junior | **Read Time:** 2 min read  
> **Source:** [https://lawsofsoftwareengineering.com/laws/sturgeons-law/](https://lawsofsoftwareengineering.com/laws/sturgeons-law/)

**90% of everything is crap.**

### Key Takeaways

- It’s like an extreme form of the Pareto Principle (80/20 rule). The bulk of what’s being put out just isn’t good, and the good stuff is the exception
- In software, there are often many features or code paths that add very little value, and the critical challenge is to find a way to maximize the high-impact 10%.
- Most new concepts or technologies fail to deliver, while the exceptional ones stand out.

### Overview

In the tech sphere, Sturgeon’s Law implies that most code or features are not necessary. Perhaps 90% of experiments or features don’t pan out, and only 10% drive real value.

As an engineer, not every line of code you write is gold; as a product manager, many features don’t delight users.

It pairs with the idea of the 10x engineer not as someone who writes 10x more code, but as someone who identifies the 10% of work that delivers 10x value. The risk isn’t the lower quality of the 90%, it’s the pretense that it isn’t. When a team considers all work to have the same value, it introduces more complexity and slows down.

In practice, Sturgeon’s Law encourages continuous refinement, assumes there’s a lot of “noise,” and focuses on finding the “signal.”

### Examples

Consider an app with 100 features. User analytics might show that users heavily use 10 of these and the rest not at all, which is exactly what Sturgeon’s Law predicts: 90% of this stuff doesn’t provide significant value.

Another example: an organization may have many project ideas to develop each quarter. According to Sturgeon’s Law, most of these ideas won’t amount to anything, but a few will prove valuable.

In the area of code reviews, a significant amount of code has been written that is neither elegant nor required. This supports the hypothesis that less code is high-quality.

### Origins

Theodore Sturgeon, a science fiction author, coined this phrase in 1957, responding to criticism that “90% of science fiction is crap.” His response: “90% of everything is crap.”

It was first published as “Sturgeon’s Revelation” in a 1957 issue of Venture magazine.

### Further Reading

- [Sturgeon's Law - Wikipedia](https://en.wikipedia.org/wiki/Sturgeon%27s_law) — Overview of the law and its origins
- [Over 50% of plugins in the WordPress repository haven't been updated in 2+ years](https://www.reddit.com/r/Wordpress/comments/1n0lnas/over_50_of_plugins_in_the_wordpress_repository/) — Reddit discussion illustrating Sturgeon's Law in the WordPress plugin ecosystem

### Related Laws

- [Goodhart's Law](planning.md#goodharts-law)
- [Gall's Law](architecture.md#galls-law)

---
