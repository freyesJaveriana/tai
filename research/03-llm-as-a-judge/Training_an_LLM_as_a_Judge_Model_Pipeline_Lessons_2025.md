# Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons

> **En [`docs/pvb.md`](../../docs/pvb.md): `[4]`** · **En [`docs/critica.md`](../../docs/critica.md): no lo cita**  
> Hu, R., Cheng, Y., Shi, X., Lin, W., Meng, L., Xia, J., & Zong, Y. (2025). *Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons*. WWW Companion 2025 - Companion Proceedings of the ACM Web Conference 2025, 228-237.  
> 
> Secciones de `pvb.md`: 1. PROBLEMA  
> Fuente convertida: `1-papersMD/2-Pilar2-Cómo/Training_an_LLM_as_a_Judge_Model_Pipeline_Lessons_2025.md`


**Archivo origen:** `1-papers/2-Pilar2-Cómo/Training an LLM-as-a-Judge Model.pdf`  
**Páginas:** 10  
**Nota:** los separadores `PAGINA n` corresponden a la página física del PDF. Los encabezados y pies de página repetidos se conservan solo en su primera aparición.


------------------------- PAGINA 1 --------------------------

# **Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons**

Yi Cheng<sup>∗</sup> ceyu.cy@alibaba-inc.com Alibaba Cloud Computing Hangzhou, China

Libin Meng<sup>∗</sup> menglibin.mlb@alibaba-inc.com Alibaba Cloud Computing Shanghai, China

Renjun Hu<sup>∗</sup> rjhu@dase.ecnu.edu.cn East China Normal University Shanghai, China Jiaxin Xia<sup>∗</sup> xjx392321@alibaba-inc.com Alibaba Cloud Computing Shanghai, China

Xing Shi Wei Lin

Yi Zong<sup>∗</sup> yzong22@m.fudan.edu.cn Fudan University Shanghai, China

shubao.sx@alibaba-inc.com weilin.lw@alibaba-inc.com Alibaba Cloud Computing Hangzhou, China

## **Abstract**

### **ACM Reference Format:**

Renjun Hu, Yi Cheng, Libin Meng, Jiaxin Xia, Yi Zong, Xing Shi, and Wei Lin. 2025. Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons. In _Companion Proceedings of the ACM Web Conference 2025 (WWW Companion ’25), April 28-May 2, 2025, Sydney, NSW, Australia._ ACM, New York, NY, USA, 10 pages. https://doi.org/10.1145/3701716.3715265

The rapid advancement of large language models (LLMs) has opened new possibilities for their adoption as evaluative judges. This paper introduces Themis, a fine-tuned LLM judge that delivers sophisticated context-aware evaluations. We provide a comprehensive overview of the development pipeline for Themis, highlighting its scenario-dependent evaluation prompts and two novel methods for controlled instruction generation. These designs enable Themis to effectively distill evaluative skills from teacher models, while retaining flexibility for continuous development. We introduce two human-labeled benchmarks for meta-evaluation, demonstrating that Themis can achieve high alignment with human preferences in an economical manner. Additionally, we explore insights into the LLM-as-a-judge paradigm, revealing nuances in performance and the varied effects of reference answers. Notably, we observe that pure knowledge distillation from strong LLMs, though common, does not guarantee performance improvement through scaling. We propose a mitigation strategy based on instruction-following difficulty. Furthermore, we provide practical guidelines covering data balancing, prompt customization, multi-objective training, and metric aggregation. We aim for our method and findings, along with the fine-tuning data, benchmarks, and model checkpoints, to support future research and development in this area.

## **1 Introduction**

The rapid advancement in large language models (LLMs) has endowed today’s most capable artificial intelligence systems with near-human cognitive abilities, including language understanding, mastery of world knowledge, instruction following, reasoning, and planning [30, 42, 43]. Often likened to revolutionary technologies such as electricity, LLMs are being deployed across various domains, including those with high-stakes [10, 34, 38]. Alongside rapid progress and widespread adoption comes an increasing concern on the large-scale potential risks [3]. As LLMs continue to evolve, evaluating their capacity [12, 15] as well as alignment with user intentions [8, 19, 21], ethical standards [18, 37], and human values [4, 11, 17] becomes pivotal.

In this study, we focus on assessing LLMs’ alignment with user intentions in open-ended tasks, _i.e.,_ the ability to accurately adhere to open-ended instructions and meet user expectations [52]. This represents the most natural usage of LLMs and such alignment is fundamental to ensuring their helpfulness [2]. While manual evaluation [8] is straightforward, it is expensive and can suffer from subjective inconsistency. Established evaluation metrics such as perplexity [16], BLUE [33], and ROUGE [26] often fall short in capturing the nuanced dimensions of alignment evaluation. Additionally, the assumption of unique ground-truth reference responses is frequently invalid in many open-ended scenarios, _e.g.,_ advice seeking and writing assistance. These gaps underscore the necessity for more sophisticated and context-aware evaluation mechanisms capable of operating automatically.

## **CCS Concepts**

• **Computing methodologies** → **Natural language processing** .

## **Keywords**

Large language models; LLM-as-a-judge; LLM evaluation

∗Equal contribution to this work. Please refer to Renjun Hu for any correspondence.

Permission to make digital or hard copies of all or part of this work for personal or classroom use is granted without fee provided that copies are not made or distributed for profit or commercial advantage and that copies bear this notice and the full citation on the first page. Copyrights for components of this work owned by others than the author(s) must be honored. Abstracting with credit is permitted. To copy otherwise, or republish, to post on servers or to redistribute to lists, requires prior specific permission and/or a fee. Request permissions from permissions@acm.org. _WWW Companion ’25, April 28-May 2, 2025, Sydney, NSW, Australia_

The continually improving capabilities of LLMs has created a new paradigm for this problem: deploying LLMs as judges to assess other LLMs, known as LLM-as-a-judge [19, 21, 25, 52]. Recent studies have demonstrated that general-purpose or specifically fine-tuned LLMs are qualified judges in at least two aspects. First, they could obtain a high evaluation agreement rate with human, matching the same

© 2025 Copyright held by the owner/author(s). Publication rights licensed to ACM. ACM ISBN 979-8-4007-1331-6/25/04

https://doi.org/10.1145/3701716.3715265


------------------------- PAGINA 2 --------------------------

WWW Companion ’25, April 28-May 2, 2025, Sydney, NSW, Australia

Renjun Hu, Yi Cheng, Libin Meng, Jiaxin Xia, Yi Zong, Xing Shi, and Wei Lin

level of human-human agreement. Second, they are able to deliver nuanced evaluations, providing more granular and explainable assessments than traditional metrics. Thus, the new paradigm has emerged as a robust and scalable solution to alignment evaluation. While promising, established judges are either general-purpose LLMs [24, 52] or collect real user instructions to construct their finetuning datasets [19, 21], being inflexible for developing evaluation ability for various LLM applications.

To this end, we introduce Themis, a judge LLM retaining flexibility for continuous development. We first detail the complete development pipeline, encompassing prompt design, data construction, fine-tuning, and performance assessment. We adopt step-by-step scenario-dependent prompts for evaluation [19, 21] and carefully design the evaluation criteria for each scenario through human-AI collaboration. These prompts strike a balance between contextenhanced accuracy and automation, compared with unified [25, 52] and instruction-based prompts [24]. A distinguishing feature of Themis is the use of controlled instruction generation. Unlike previous work that relies on existing instruction sets [51], we develop two instruction synthesis methods: reference-based questioning and role-playing quizzing, which could generate or supplement instruction data in a controlled manner. The step-by-step evaluation prompts and instruction synthesis methods together allow to comprehensively induce the evaluative skills from state-of-the-art LLMs (says, GPT-4), which are distilled into Themis through supervised fine-tuning [29]. The combination also features flexibility for continuous development to fulfill real evaluation requirements. We create two human preference benchmarks for meta-evaluation. The results reveal that Themis achieves comparable and slightly worse performance on the in- and out-of-distribution benchmarks, respectively, using less than 1% of parameters compared with its teacher GPT-4, and outperforms all other tested (judge) LLMs. These validate the effectiveness of the pipeline.

We next conduct a series of in-depth analyses of Themis from a scenario-centric perspective, which yield several key insights that deepen our understanding of the paradigm. Our examination reveals a positive correlation between LLMs’ capacity and the corresponding evaluation performance for scenarios: Themis performs relatively well in open-ended scenarios, where LLMs’ inherent capabilities are better suited, whereas it is less effective in closed-ended scenarios. Additionally, we analyze the impacts of reference answers on LLM-based evaluation. Our findings indicate that reference answers can improve evaluations in closed-ended scenarios, compensating the defect of direct evaluations, but have only negligible or even detrimental effects in open-ended scenarios. Furthermore, we investigate how fine-tuning data composition and scaling affect model performance. Surprisingly, we find that pure knowledge distillation from teacher LLMs does not guarantee performance improvement through scaling, indicating the inherent quality flaw in model-generated fine-tuning data. This poses a significant challenge for practical data engineering. In response to it, we propose a mitigation using instruction-following difficulty as a metric to guide data filtering.

We finally share practical lessons learned from Themis and offer some advices for model optimization. These include creating more balanced fine-tuning datasets, supporting custom evaluation prompts to enhance generalization while minimizing memorization,

and employing multi-objective training for further improvement. We also recommend metric aggregation to provide a single score for assessing optimization effectiveness, which is critical to maintain development efficiency for building a versatile LLM judge. Themis currently offers evaluation service on Alibaba Cloud through API,<sup>1</sup> compatible with Python openai SDK. We open-source our data, benchmarks, and model checkpoints to support future research.<sup>2</sup>

## **2 Related Work**

LLMs have greatly revolutionized the field of natural language processing. Classic overlapping-based methods [26, 33] are no longer suitable for evaluating today’s LLMs. Human evaluation suffers from its high cost and is time-consuming [8]. Currently, automatic LLM evaluation could be roughly divided into three categories.

**Evaluation on static benchmarks** . Static benchmarks have been developed to assess the performance of LLMs across various tasks, such as language understanding [12], world knowledge [15, 53], reasoning [49], coding [7], and math [13]. These benchmarks usually consist of objective, _e.g.,_ multi-choice, questions designed to rigorously evaluate specific abilities. Metrics like accuracy could then serve as valuable references for model comparison and advancement. However, evaluation on static benchmarks has its limitations. A notable shortcoming is that the tested metrics only capture LLMs’ performance on predefined tasks with closeended outputs, resulting in a gap between user perceptions of LLMs’ usefulness in real-world applications. Additionally, static benchmarks may inadvertently incentivize models to over-fit rather than developing generalizable ability [5, 54]. Recent efforts have sought to expand the variety of benchmarks to include more diverse and up-to-date knowledge [28] or reasonable perturbations [20] for assessing genuine capacity.

**Human-inspired evaluation** . Techniques in the second category treat LLMs as if they possess human-like qualities, utilizing methodologies originally developed for human assessments to evaluate these models. This types of approaches often focus on the social characteristics of LLMs, such as creativity [50], values [4, 11, 17], ethical standards [18, 37], trustworthiness [40], etc.

**LLM-as-a-Judge** . The concept of utilizing LLMs as judges has emerged as a new evaluation paradigm [25, 52]. This innovative approach leverages the intrinsic capabilities of LLMs to provide fine-grained evaluations, and it has been demonstrated that LLMs can achieve high agreement rates with human evaluators [24, 52], effectively serving as substitutes for traditional evaluation metrics. Along the line, some studies have devoted to constructing instruction sets for evaluation, with those large-scale [51], in the wild [24], and challenging [23] standing out. Others have explored fine-tuning an LLM as judge, which has also been verified effective and more economical [19, 21, 44].

Our work belongs to the third category, differing from related work in two aspects. Methodologically, Themis integrates a combination of step-by-step evaluation prompts and controlled instruction generation, featuring better flexibility to develop required evaluation ability. Empirically, we provide both scenario-centric

> 1https://www.alibabacloud.com/help/en/pai/user-guide/judge-model/

> 2https://github.com/aigc-apps/pai-judge-themis


------------------------- PAGINA 3 --------------------------

insights and lessons for LLM-as-a-judge from an industrial perspective. Notably, the observed quality flaw in model-generated data and our mitigation present a unique complement to the area.

## **3 Development Pipeline**

In this section, we present the complete development pipeline of Themis. Strategically, Themis adopts scenario-dependent evaluation prompts, employs two methods for controlled instruction generation, and learns from GPT-4 rationales. We establish two human preference benchmarks to quantify Themis’s performance.

## **3.1 Prompt Design**

The effectiveness of LLM-as-a-Judge is significantly influenced by the design of evaluation prompts. Previous studies have explored three types of prompts: unified [25, 52], scenario-based [19, 21], and instruction-based [24]. We choose scenario-based prompts for Themis because they provide the necessary context-awareness for instruction-specific evaluations while imposing reasonable additional requirement, _i.e.,_ a scenario classification model, to achieve evaluation automation.

We employ human-AI collaboration to designed scenarios and their corresponding judge criteria. Initially, we draft a proposal of common LLM use scenarios, including their names and descriptions, and solicit suggestions from an advanced LLM, such as GPT-4. In a subsequent iteration, we request the same LLM to output its scenario design based on both the initial human proposal and its own modification suggestions. From this process, we finalize 10 scenarios from the initial 15. These include: _three question-answer scenarios_ (close QA, open QA, and math-related QA), _three writing scenarios_ (creative writing, informative and professional writing, and rewriting), and _four professional scenarios_ (translation, reading comprehension and extraction, role-playing, and programmingrelated). For each chosen scenario, we follow the same iterative process to derive the judge criteria. This involves an initial human proposal, suggestions from the AI, a revised AI proposal incorporating these suggestions, and a final human-edited version. Detailed scenario descriptions and the chosen judge criteria (81 in total) are provided in Appendix A, as well as a scenario comparison with Llama 3 [1] which empirically justifies our scenario design through human-AI collaboration.

We then develop the scenario-based evaluation prompts. Similar to previous work, we support three variants of judgement: single answer grading, reference-guided grading, and pairwise comparison. The prompt template for single answer grading is presented in Table 1, which consists of five components separated by blank lines: (1) task description with scenario information emphasized, (2) grading guidelines, (3) the evaluation input data, (4) evaluation steps, and (5) output requirement and format. The templates for the other two variants are similar, with slight differences in input data and output ratings. These detailed, step-by-step prompts offer several benefits. First, they provide judge LLMs with concrete instructions on how to perform evaluations, including both general grading tiers and steps, and scenario-specific criteria. Second, they encourage LLMs to elucidate the reasons for their ratings, which enhances learning efficiency during model training and improves interpretability during deployment. To perform evaluations using

**Table 1: Prompt template for single answer grading.**

|Your task is to evaluate the quality of AI responses. You are well aware that<br>when a user issues an instruction of [{scenario name}] (the definition<br>is:{scenario description}), an AI assistant’s response should meet<br>the following criteria (listed in descending order of importance):<br>[Criteria Begin]<br>{judge criteria of the scenario}<br>[Criteria End]|
|---|
|The grading uses a five-tier system (1–5), the meanings of each tier are:<br>[Grading Tiers Begin]<br>1 The response has significant flaws, totally deviates from the criteria,<br>and should not be seen in practice.<br>2 The response has parts that meet the criteria and can be adopted, but<br>as a whole, the quality is not sufficient.<br>3 The response has a mix of strengths and weaknesses, with strengths<br>overall outweighing the weaknesses within the evaluation criteria.<br>4 The response is of acceptable quality, overall meets the criteria, and<br>has few minor issues that can be improved. When a reference answer is<br>given, this tier represents the quality shown by the reference answer.<br>5 The response is excellent, strictly meets the criteria in all aspects. When<br>a ref answer is given, this tier represents a quality superior to the answer.<br>[Grading Tiers End]|
|Regarding a user instruction of [{scenario name}] , we have collected<br>the following AI assistant response. Please evaluate this response against<br>the known criteria for the current scenario and provide your assessment.<br>Below are the user instruction and the assistant’s response data:<br>[Data Begin]<br>***<br>[User Instruction]:{instruction}<br>***<br>[Response]:{response}<br>***<br>[Data End]|
|You need to follow these steps to evaluate the above response:<br>1. Recall the relevant AI assistant response criteria and carefully read and<br>understand the response to be evaluated.<br>2. Identify from all criteria the key ones for the current user instruction<br>and response, including those that performed well and those that did not.<br>3. Besides the given criteria, add any other important criteria that you<br>think are necessary for evaluating the current user instruction response.<br>4. Based on your final selection of criteria, assign scores (1–5) to each<br>criterion, and provide an overall score by weighting all sub-scores.|
|Think carefully and then provide your conclusion. Your response should<br>keep the ‘[[’ and ‘]]’ symbols in the output:<br>I believe the overall rating of this response is [[a score between 1–5]],<br>and the reasons are as follows.<br>Strengths of the current response:<br>(List each point that you think is well done in the current response,<br>providing [[a score between 1–5]] for each point...)<br>Shortcomings of the current response:<br>(List each point that you think is lacking in the current response, provid-<br>ing [[a score between 1–5]] for each point...)|

these scenario-dependent prompts, we have fine-tuned an LLM for scenario classification, _i.e.,_ assigning a scenario to each user instruction. Details of this model are provided in Sec. 3.3.


------------------------- PAGINA 4 --------------------------

## **3.2 Data Construction**

We next outline the data construction pipeline for the supervised fine-tuning [31] of Themis, including collecting user instructions, their corresponding responses, and evaluations of these instructionresponse pairs. The primary challenge is gathering user instructions, as responses and evaluations can be automatically generated by LLMs. Typical methods for collecting user instructions involve utilizing existing instruction sets [19, 21, 51] or generating instructions from a small set of seed examples [41, 45]. However, these methods may not adequately balance instruction distribution across scenarios, potentially impacting the performance of judge LLMs due to unbalanced or insufficient data. To address this, we introduce the idea of controlled instruction generation, employing referencebased questioning and role-playing quizzing.

**Reference-based questioning** . Our first method leverage LLMs’ generative ability to synthesize user instructions for specific scenarios based on reference texts. We achieve this efficiently by finetuning a questioning model [46] using data generated by GPT-4. We adopt a prompt (available in an extended version due to the space constraint) specifies the scenario name and description to guide question synthesis. A piece of reference text is also provided. Both of them enhance controllability for the process. It also outlines synthesis requirements, provide examples from a small set of manually crafted seed instructions, and requests GPT-4 to generate five instructions at a time. We manually validate these outputs and use the filtered data to fine-tune the questioning model.

**Role-playing quizzing** . While the reference-based method excels in generating questions for seven scenarios, it struggles with instruction adherence and quality for the remaining three scenarios, particularly in scenarios like math-related QA and programming, where reference text suitability is crucial. To this end, we propose the role-playing quizzing method, which leverages LLMs’ ability to act as test writers to generate instructions for these challenging scenarios. This method specifies quiz-related information such as difficulty level, audience, subject, topic, and task to improve controllability. Detailed prompts for this method will also be provided in a future extended version.

These two methods together ensure a balanced and comprehensive collection of user instructions across diverse scenarios. We then gather responses to these instructions from LLMs of varying capacity, including ChatGLM3-6B, Baichuan2-13B, Yi-34B, Qwen-72B, and GPT-3.5-turbo. These instruction-response pairs are evaluated with GPT-4 using the evaluation prompts developed earlier, and we use the detailed evaluation outputs to fine-tune Themis.

## **3.3 Fine-tuning**

We now detail the fine-tuning process for our models. We choose the Qwen-2 series base models [43] as the foundation models. The fine-tuning data are summarized in Table 2. All training tasks are executed on Nvidia H800 GPUs, utilizing DeepSpeed ZeRO-3 [35] to optimize GPU memory usage and accelerate training.

**Scenario classification LLM** . We manually label 18,874 records for fine-tuning the scenario classification model. Each labeled record is converted into a prompt. This prompt enumerates the scenarios with both name and description, specifies a user instruction, and ask the LLM to classify a scenario for the instruction. We used the

**Table 2: Statistics of fine-tuning data over scenarios. SC, Q, UI, and E (S/P) represent for scenario classification, questioning, synthesized user instructions, and evaluation records by single answer grading and pairwise comparison.**

|**Scenarios**|**#SC**|**#Q**|**#UI**|**#E (S/P)**|
|---|---|---|---|---|
|Close QA|3,433|2,216|2,498|1,411/500|
|Open QA|1,794|751|923|361/500|
|Math-related QA|1,435|/|3,651|1,616/500|
|Creative writing|2,173|1,999|1,994|895/500|
|Info&Prof writing|1,505|1,145|1,275|517/500|
|Rewriting|2,154|1,156|1,830|939/500|
|Translation|1,998|1,045|1,618|800/500|
|Reading C&E|1,316|/|3,128|1,345/500|
|Role-playing|2,163|1,588|2,112|975/500|
|Programming|903|/|2,945|1,141/500|
|Total|18,874|9,900|21,974|10,000/5,000|

labeled scenarios for fine-tuning, which teaches the LLM to classify future user instructions. We fine-tune a 7B model for scenario classification in Themis, balancing performance and serving costs. The model is trained over 5 epochs on 8 GPUs, using a batch size of 64, a learning rate of 1e-5, and a warmup ratio of 0.1. We also manually label the scenarios on the Alignbench [27] dataset to quantitatively evaluate the performance of the fine-tuned model. The dataset contains 683 selected real user instructions and is not included in the fine-tuning process. Our fine-tuned 7B model obtains an accuracy of 93.1% on this test set, indicating that it could choose appropriate scenario-based prompts for evaluation.

**Questioning LLM** . We use Wikipedia data as reference text and obtain 9,900 questions across seven scenarios after the manual validity check. This data is employed to fine-tune the questioning model, using a prompt similar to the one for data synthesis but generating one question at a time. We fine-tune a 14B model for this task, running the training on 8 GPUs with a batch size of 512, a learning rate of 1e-5, and a warmup ratio of 0.1 for 3 epochs.

**Main model** . We synthesize 21,974 user instructions with our controlled instruction generation methods. Each instruction is paired with five LLM responses, which are then used to create evaluation records with GPT-4. Specifically, we use 10,000 instructionresponse pairs for single answer grading and another 10,000 pairs for pairwise comparison, resulting in a total of 15,000 evaluation records. To balance scores and pairwise ratings, we sample 6,404 single-answer records and 3,803 pairwise records, and we double the pairwise records with order replacement to reduce order bias. Ultimately, we obtain 6 _,_ 404 + 2 × 3 _,_ 803 = 14 _,_ 010 records for supervised fine-tuning of the main model. We train a 14B model for 3 epochs on 16 GPUs, using a batch size of 128, a learning rate of 2e-5, and a warmup ratio of 0.1.

## **3.4 Performance Assessment**

**Benchmarks** . We create two human preference benchmarks for performance assessment. (1) Alignbench [27] contains 683 manually selected real user instructions and we extend the data with a scenario label and five responses by the same set of LLMs in Sec. 3.2


------------------------- PAGINA 5 --------------------------

**Table 3: Performance comparison on benchmarks.**

|**Judge**|**Alignb**<br>**MAE**↓|**ench (3,393)**<br>**Agr**(2_,_2) ↑|**Syn**<br>**MAE**↓|**UI (4,000)**<br>**Agr**(2_,_2) ↑|
|---|---|---|---|---|
|AutoJ-13B [21]|/|/|/|/|
|CritiqueLLM-6B [19]|1.297|0.346|1.259|0.346|
|Qwen-14B|1.320|0.366|1.035|0.437|
|Qwen-max|1.131|0.424|0.840|0.497|
|GPT-4|**0.685**|**0.595**|**0.664**|**0.590**|
|Themis|0.756|0.559|0.673|0.582|

<!-- Start of picture text -->
0.80<br>R = 0.822 0.71<br>0.71<br>0.64<br>0.62 0.57 R = 0.426<br>0.53 0.50<br>0.44 0.43<br>2.44 2.85 3.25 3.66 2.92 3.23 3.53 3.84<br><!-- End of picture text -->

**Figure 1: The positive correlation between scenario Agr** (2 _,_ 2) **and average labeled scores.**

to each instruction. We then recruit annotators to assign three five-tier scores (1–5) to each instruction-response pair, giving the same score descriptions and scenario criteria as Themis. Scores are then aggregated through majority voting, with the average rounded to the nearest integer in cases of discrepancy, resulting in 3,393 scored instruction-response pairs across eight scenarios. (2) SynUI consists of 2,000 synthesized user instructions from the total 21,974. For each instruction, we randomly select two responses and apply the same manual annotation process as for Alignbench, leading to 4,000 scored instruction-response pairs covering all ten scenarios. Importantly, the instructions used for performance assessment are distinct from those used in fine-tuning.

**Metrics** . We utilize two metrics to quantify performance. (1) MAE measures the average deviation between human labeled and LLM predicted scores. (2) Agr( _𝑝,𝑞_ ) is a general agreement metric that accommodates weighted agreements and non-exact matches. Specifically, Agr( _𝑝,𝑞_ ) =<sup>�</sup> ( ˆ _𝑦,𝑦_ )∈T<sup>_𝐴𝑞_</sup> _𝑝_<sup>(</sup><sup>_𝑦,𝑦_ˆ)/|T |</sup><sup>_,_where Tis the set</sup> of predicted and labeled score pairs and _𝐴_<sup>_𝑞_</sup> _𝑝_<sup>(</sup><sup>_𝑦,𝑦_ˆ)= 1/(|</sup><sup>_𝑦_ˆ−</sup><sup>_𝑦_| + 1)</sup><sup>_𝑞_</sup> if | _𝑦_ ˆ − _𝑦_ | _< 𝑝_ , and 0 otherwise. Note that Agr(1 _,_ ∗) is the same to accuracy and we use Agr(2 _,_ 2) for our assessment, which assigns an agreement of 0.25 when | _𝑦_ ˆ − _𝑦_ | = 1.

**Performance on benchmarks** . Table 3 shows the performance of Themis compared to two fine-tuned judges and three foundation LLMs on our benchmarks. Note that we unify the evaluation prompts for all tested LLMs, _i.e.,_ using the same ones as Themis, to keep the scoring criteria consistent with annotators and avoid scenario mapping for judge baselines. We find that AutoJ-13B encounters prompt generalization issue and does not give valid evaluation results. CritiqueLLM-6B could complete the task for approximately 70% of the records, but is worse than other methods. We note that these results are for reference-purpose only as prompts are very important for fine-tuned judges.

Recall that Themis is fine-tuned from Qwen-14B and we find that it outperforms Qwen-14B by 34.3% on average, demonstrating the effectiveness of our training pipeline. Additionally, Themis exceeds Qwen-max by 22.9%, despite being smaller in size. This indicates that fine-tuning an LLM for evaluation purposes provides substantial benefits. Finally, we find that our training pipeline is generally efficient in skill distillation: Themis using less than 1% parameters shows only 1.4% and 8.4% worse performance than its teacher GPT-4 model on the in-distribution SynUI and out-of-distribution Alignbench benchmarks, respectively. It is worth noting that GPT-4 remains the most competitive baseline in this area [44, 52], and the achievement of Themis deserves affirmation.

**Performance on a real evaluation task** . Themis has been deployed online, where it is used for pairwise comparison in chat response evaluations, _i.e.,_ judge models should compare a pair of responses given a multi-turn dialog and decide which one is better or both are tied. In a set of 397 test records, the accuracy rates for (Qwen-72B, Themis, Qwen-max, GPT-4) are (46.6%, 71.8%, 73.8%, 76.6%), respectively. Subsequent optimizations have improved the accuracy of Themis to 75.3%. These performance results together underscore the practical value of Themis for alignment evaluation.

## **4 Insights from Scenario-centric Analysis**

**Exp-1. Detailed performance across scenarios** . We first investigate the performance of Themis across different scenarios and the detailed results of single answer grading Agr(2 _,_ 2), as well as the corresponding z-value, on our benchmarks are reported in Table 4. Z-values exceeding 0.5 and falling below -0.5 are highlighted in bold and underlined, respectively. The results reveal that Themis generally excels in open-ended scenarios such as role-playing, open QA, creative writing, and informational and professional writing. On the other hand, its performance diminishes in close-ended scenarios like close QA and math-related QA, which demand higher knowledge and reasoning capabilities for accurate responses and evaluations. Additionally, we observe a positive correlation between scenario-based Agr(2 _,_ 2) and the average labeled scores ( _i.e.,_ avg. _𝑦_ ) of our responding LLMs on these scenarios: the Pearson correlation coefficient is 0.822 and 0.426 on Alignbench and SynUI, respectively (see Fig. 1). This suggests that the inherent capacity of LLMs significantly influences their effectiveness as judges.

**Insight 1: The evaluative performance of LLMs positively correlates with their inherent capacity.**

**Exp-2. The impacts of reference answers** . The availability of reference answers would make the evaluation tasks more manageable for humans. Analogically, we next explore how reference answers affect alignment evaluation with LLMs. Alignbench includes a reference answer drafted by GPT-4 and refined by human for each instruction, while SynUI uses GPT-4’s responses as reference answers. The results of reference-guided grading Agr(2 _,_ 2), as well as the resulting improvement by reference answers, are also presented in Table 4, from which we find the following. First, reference answers improve the Agr(2 _,_ 2) of Themis by 0.059 on Alignbench, but have minimal overall impacts on SynUI. This difference likely arises from Alignbench’s higher answer quality and


------------------------- PAGINA 6 --------------------------

**Table 4: Performance of Themis with single answer grading (SAG) and reference-guided grading (RGG) for different scenarios. Note that we report Agr** (2 _,_ 2) **for columns SAG and RGG, z-val is calculated on SAG, and** Δ = **RGG** − **SAG.**

|**Scenario**|||**Align**<br>|**bench**|||||**Syn**<br>|**UI**|||
|---|---|---|---|---|---|---|---|---|---|---|---|---|
||**#Tests**|**SAG**|**z-val**|**avg.**_𝑦_|**RGG**|Δ|**#Tests**|**SAG**|**z-val**|**avg.**_𝑦_|**RGG**|Δ|
|All|3,393|0.559|-0.223|2.914|0.618|0.059|4,000|0.582|-0.092|3.450|0.584|0.002|
|Close QA|1,503|0.484|-0.876|2.785|0.576|0.092|510|0.548|-0.555|2.929|0.561|0.013|
|Open QA|190|0.791|**1.799**|3.659|0.797|0.006|138|0.616|0.371|3.609|0.717|0.101|
|Math-related QA|555|0.522|-0.545|2.444|0.589|0.067|716|0.433|-2.120|3.500|0.455|0.022|
|Creative writing|130|0.560|-0.214|2.962|0.55|-0.010|386|0.659|**0.957**|3.653|0.698|0.039|
|Info&Prof writing|242|0.697|**0.980**|3.311|0.696|-0.001|204|0.566|-0.309|3.152|0.625|0.059|
|Rewriting||||/|||338|0.538|-0.691|3.210|0.558|0.020|
|Translation|50|0.510|-0.650|2.720|0.645|0.135|284|0.556|-0.446|3.451|0.539|-0.017|
|Reading C&E|153|0.449|-1.181|3.045|0.513|0.064|574|0.702|**1.542**|3.645|0.689|-0.013|
|Role-playing|570|0.689|**0.910**|3.255|0.705|0.016|366|0.653|**0.875**|3.377|0.59|-0.063|
|Programming||||/|||484|0.623|0.467|3.837|0.571|-0.052|

**Figure 2: Performance of fine-tuning with single scenario data. Each column denotes a model fine-tuned using data from a single scenario, with** ∅ **being the baseline without fine-tuning. Each row reports the performance of different models on a specific scenario.**

instruction difficulty. Moreover, we find the influence of reference answers varies between open and close-ended scenarios: they tend to improve performance in close-ended scenarios but have negligible or negative effects in open-ended ones. For instance, the average improvement on Alignbench is 0.090 for close-ended ( _i.e.,_ those underlined) and 0.007 for open-ended scenarios ( _i.e.,_ those in bold). Similar trends are noted on SynUI, where reference answers sometimes mislead Themis ( _i.e.,_ leading to negative improvement), particularly in open-ended scenarios, potentially diminishing the evaluation of semantically diverse but good responses.

**Insight 2: Themis’s performance in close-ended scenarios can be enhanced with high-quality reference answers.**

**Exp-3. Fine-tuning with single scenario data** . Previous research has validated that data composition significantly impacts

model performance during pre-training and fine-tuning [9, 48]. As a basis for exploring these effects for LLM-as-a-Judge, we first examine the performance of fine-tuning with data from individual scenarios. We randomly sample 800 evaluation records for each of the ten scenarios, ensuring a relatively balanced distribution of grading scores and pairwise ratings. We then fine-tune ten judge models, each trained on data from a single scenario, and assess their judging performance for all scenarios on our two benchmarks. We report the combined performance metric, _i.e.,_ averaged multiple metrics on both benchmarks, in Fig. 2, where higher numbers indicate better performance.

From the table we find that all fine-tuned models outperform the baseline foundation model (column ∅), highlighting the general benefit of fine-tuning for LLM-as-a-Judge. However, the impact of data from different scenarios varies. For example, data from informative and professional writing (column IPW) enhances the evaluation performance across all scenarios; where data from close QA (column CQA) lead to performance deterioration in several scenarios like open QA (OQA) and translation (T). This deterioration likely results from mismatches in evaluation criteria and the structured quality issues of LLM-generated fine-tuning data. Surprisingly, fine-tuning on data from translation (T) and programming (PG) scenarios leads to decreased performance on their respective tasks, further evidencing the limitations of data quality. These results suggest that data from different scenarios can have both positive and negative effects on evaluation performance.

**Insight 3: Fine-tuning generally benefits LLM-as-a-Judge, but careful data engineering at the scenario level is crucial due to the varying synergistic and inhibitory effects of different scenario data.**

**Exp-4. Data composition and scaling** . In the last set of analysis, we investigate the effects of data composition and scaling on model performance. Following the method in [39, 47], we use K-means algorithm to group scenarios to manage the number of required tests. We employ the columns of Fig. 2 as the clustering features, exclude the close QA scenario due to its minimal overall improvement, and choose _𝐾_ = 3, resulting in the clusters (A: MQA, GP), (B: IPW, RW, T, RP), and (C: OQA, CW, RCE). Intuitively, scenarios within same clusters exhibit similar influence on model’s


------------------------- PAGINA 7 --------------------------

**Figure 3: Impacts of data composition.**

**Figure 4: Impacts of scaling** **_w.r.t._ data selection strategies.**

evaluation performance after fine-tuning, suggesting that mixing data within clusters is feasible.

To assess the impacts of data composition, we fine-tune multiple models with the same number ( _i.e.,_ 800) of training each, varying the proportions of records from different clusters. The overall performance of resulting models are reported in Fig. 3, with varying ratio of (A+B)/C on the left and varying ratio of A/B when (A+B)/C=1/2 on the right. From the results we find that data composition significantly affects evaluation performance. For example, increasing (A+B)/C from 1/2 to 1 decreases performance from 0.4 to 0.2. Optimal data composition allows using as little as 6% of the fine-tuning data to achieve near-equivalent performance to using the full dataset, _e.g.,_ 0.3959 vs. 0.4005 across all scenarios. However, it also turns out that the impact of varying ratios can be unpredictable, likely due to the inherent flaws in LLM-generated data. It requires numerous trials to identify an effective composition plan

Next, we investigate data scaling, a primary means for boosting LLM abilities [36]. Previous results suggest that scaling with random data selection may not work as expected. We then explore advanced data selection strategy used in conjunction with data scaling for our task. Specifically, we choose the Instruction-Following Difficulty [22] (IFD) metric for this purpose, which is designed to to measure how much help the instruction can provide to the generation of the corresponding response. Formally, given instruction _𝑄_ and its corresponding fine-tuning answer _𝐴_ , the IFD score of the instruction-answer pair is defined as:

where _𝜔𝑖_ is the _𝑖_ -th token of _𝐴_ and _𝜃_ represents an LLM model. Higher IFD scores indicate the inability for the model to align responses to the corresponding instructions. We then calculate the IFD score of each fine-tuning record and observe that records associated with higher IFD scores are generally hard to evaluate, often necessitating the agile utilization of knowledge or deep understanding of instructions. The original work proposes to filter data with IFD _>_ 1 and then select data in descending order of IFDs. Alternatively, we suggest only filtering data with extremely high IFD, _e.g.,_ with scenario-based z-score _>_ 3.

Figure 4 reports the overall performance results of data scaling under three data selection strategies including random, original IFD method, and IFD with z-score filtering. Note that we fix the best data composition ratios identified in the previous set of tests. From the figure we find that scaling data under the random strategy does not assure increased performance. Indeed, it reaches to a peak at the

beginning, _i.e.,_ using 800 records, in out tests. On the other hand, the trends of the two IFD-based strategies are more predictable, keeping increasing before using 3,200 records. Among the two, the IFD + z-score method is better. Finally, we obtain the best model using 3,200 fine-tuned record, with an overall performance of 0.4095 _vs._ 0.4005 fine-tuned on all data.

**Insight 4: Data composition and scaling significantly affect the performance of fine-tuned models. However, identifying the optimal combination is challenging due to the high variability in impacts. The IFD-based data selection strategy shows promise for further exploration.**

## **5 Practical Lessons**

This section shares the practical lessons we learn during developing and optimizing the performance of Themis. Note that the numbers in this section are not evaluated on the latest benchmarks, thus may be inconsistent with those in previous sections.

**Balancing fine-tuning data** . We use full parameter fine-tuning to speedup model adaption and we find that the distribution of evaluation scores and pairwise ratings of fine-tuning data severely influences the rating bias of the obtained model. For instance, we fine-tuned an earlier version of Themis with all single answer grading evaluation records, and the resulting MAE and Agr(2,2) are 1.068 and 0.455 on the Alignbench benchmark, much worse than its teacher GPT-4 with 0.868 and 0.509. During model diagnosis we observe that the model has an extreme high trend to rate response with score 4. We check the distribution of scores in the fine-tuning data and find that evaluation records with score 4 account for approximately 56%. We then down-sample these records to achieve a more balanced score distribution, leading to optimized MAE and Agr(2,2) with 0.908 and 0.467. And the predicted scores are less biased to a specific one.

**Supporting custom evaluation prompts** . Recall Table 1 that our scenario-based prompts use fixed criteria, steps, and a five-tier rating system for evaluation. During the deployment of Themis, our initial users request for supporting custom prompts for criteria and rating systems. To this end, we have constructed a custom prompt generation procedure which augments required data without extra API usage for GPT-4.

<u>(1) Rephrasing criteria and descriptions.</u> Referring to [32], we employ an LLM to paraphrase existing criteria, requiring the paraphrased names and descriptions to have low textual similarity to


------------------------- PAGINA 8 --------------------------

<!-- Start of picture text -->
I believe the overall rating for this response is [[3]], for the following reasons.<br>The advantages of the current response:<br>1.Text Coherence: The response is coherent in structure, gradually unfolding the<br>scenarios that might occur once environmental protection is taken seriously, providing<br>readers with a clear understanding path. [[4]]<br>…<br>CrossEntropy Loss :<br>CEL<br>Vocab Prob. Ground Truth<br>Embedding<br>Similarity Loss : MSE/cos<br>Output Emb. Input Emb.<br><!-- End of picture text -->

**Figure 5: Our multi-objective training method.**

the original, while maintaining semantic consistency. After manual check the results, we obtain over 2,400 name-description pairs as complement to the original ones. We then replace the original criteria with the corresponding rephrased ones.

<u>(2) Diversifying effective criteria in evaluations. To accommodate</u> possibly various user-defined criteria, we employ a random sampling strategy of effective criteria in each evaluation to enhance the generalization of our model. Note that Themis performs evaluation by firstly assigning scores for each criterion and then aggregating these scores to derive a final score. Consequently, criteria downsampling necessitates recalculation of the final scores. To achieve this, we have developed a method wherein we extract scores from existing evaluation records. We then train a regression model to predict the final score from each criteria grade. Results show that such a simple regression model achieves a MAE of only 0.12 evaluated on a reserved validation set. Subsequently, we derive extra evaluation records by down-sampling effective criteria and updating the final scores with the regressed.

<u>(3) Using alternative rating systems. Except for the 5-tier rating,</u> other systems are also popular for evaluation, such as binary (0-1 or 1-2), 3-class (1-3), and 10-class (1-10) ratings. To accommodate them, we transform the original scores into other systems with heuristic score mapping rules.

<u>(4) Hybrid customization. To achieve optimal model performance,</u> we mixed the aforementioned operations in different proportions, resulting in our final augmented fine-tuning data.

While supporting custom evaluation prompts is initially a functional requirements, we also observe improvement on performance: the MAE exhibited reductions from (0.699, 0.703) to (0.684, 0.676) and the Agr(2,2) are improved from (0.577, 0.569) to (0.586, 0.581) on the two benchmarks, respectively. Research on learning theory of LLMs provides a plausible explanation for the improvement. Note that fixed prompts lead to duplicated fine-tuning data, which will strengthen the memorization effect while weakening the generalization ability of LLMs [6]. Custom evaluation prompts could be regarded as a de-duplication step, enhancing the generalization of the resulting models. Similarly, we also observe the improvement by using a large batch size.

**Enabling multi-objective training** . In the standard SFT process, LLMs learn from predicting the exact next tokens by minimizing the cross entropy loss. However, we note that not all tokens

in the evaluation output need to be “perfectly" predicted. Take the output in Fig 5 as an example. The content in black is scores and format-related text, and we require these words to be predicted accurately. On the other hand, the words in blue are the explanation for the specific score, for which we could tolerate more noises as long as the predicted content is semantically similar to the target.

This idea inspires a multi-objective training method illustrated in Fig 5. Specifically, we first label each output tokens with either SFT or Sim. For SFT tokens, we still minimize the cross entropy loss between the the predicted and ground-truth logits. For Sim tokens, we minimize the difference between the embeddings of the top-1 predicted and ground-truth tokens. We find that this training method reduces the MAE from (0.684, 0.676) to (0.673, 0.652) and improves Agr(2,2) from (0.586, 0.581) to (0.594, 0.591) on the two benchmarks, respectively.

**Unifying performance metrics** . We finally share a lesson for development efficiency. During our deployment of Themis, a longterm challenge is to determine which fine-tuned checkpoint, or equivalently the corresponding optimization technique, is better. Recall that Themis supports three variants of evaluations, which is a tradition for the LLM-as-a-Judge paradigm, as well as we create two benchmarks and use two metrics for performance assessment. Putting these together, we need to compare more than 10 numbers to come to a decision, which is not easy. Indeed, we have had a lot of controversies for which one is better within our team. Later, we decide to aggregate all performance metrics into one to close controversies. The most straightforward method is to use the average score. However, we find this is unfair due to the different effective scales for metrics. For instance, it is much harder to optimize the Agr(2,2) by 0.1 than MAE. In this case, using average score will let MAE dominate the choice of optimization directions. To address this, we perform a linear transformation on the original metrics such that random guessing is mapped to 0 and the best performance metric is mapped to 1. Averaging the transformed metrics gives us a fair overall performance metric which help us choose promising optimization strategies.

## **6 Conclusion**

In this paper, we developed an LLM judge model named Themis for user intent alignment evaluation. We first detailed the development pipeline of Themis. Specifically, it utilized scenario-dependent evaluation prompts, incorporated two innovative methods for controlled instruction generation, and distilled evaluative skills from GPT-4. Results on our human preference benchmarks demonstrated the effectiveness of our training pipeline: Themis could offer automatic and contextually informed evaluations with an accuracy close to GPT-4 while using much lower serving costs. We also presented key insights which could enhance the understanding of the LLM-asa-judge paradigm. To advance further research and development, we shared our experience for performance optimization and committed to release our data, benchmarks and model checkpoints to the community. A couple of problems deserve further investigation. We are exploring multi-agent collaboration and human-in-the-loop to mitigate the data quality issues of LLM-generated SFT data. In addition, we seek to train foundation models specific for LLM-as-ajudge to boost generalization.


------------------------- PAGINA 9 --------------------------

## **References**

- [1] Meta AI. 2024. _Introducing Meta Llama 3: The most capable openly available LLM to date_ . Retrieved July 23, 2024 from https://ai.meta.com/blog/meta-llama-3/

- [2] Yuntao Bai, Andy Jones, Kamal Ndousse, Amanda Askell, Anna Chen, Nova Dassarma, Dawn Drain, Stanislav Fort, and et al. 2022. Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback. _ArXiv_ abs/2204.05862 (2022).

- [3] Yoshua Bengio, Geoffrey Hinton, Andrew Yao, Dawn Song, Pieter Abbeel, Trevor Darrell, Yuval Noah Harari, Ya-Qin Zhang, Lan Xue, Shai Shalev-Shwartz, Gillian Hadfield, Jeff Clune, Tegan Maharaj, Frank Hutter, Atılım Güneş Baydin, Sheila McIlraith, Qiqi Gao, Ashwin Acharya, David Krueger, Anca Dragan, Philip Torr, Stuart Russell, Daniel Kahneman, Jan Brauner, and Sören Mindermann. 2024. Managing extreme AI risks amid rapid progress. _Science_ 384, 6698 (2024), 842– 845.

- [4] Pablo Biedma, Xiaoyuan Yi, Linus Huang, Maosong Sun, and Xing Xie. 2024. Beyond Human Norms: Unveiling Unique Values of Large Language Models through Interdisciplinary Approaches. arXiv:2404.12744 [cs.CL]

- [5] Sebastian Bordt, Harsha Nori, and Rich Caruana. 2024. Elephants Never Forget: Testing Language Models for Memorization of Tabular Data. arXiv:2403.06644 [cs.LG]

- [6] Hoyeon Chang, Jinho Park, Seonghyeon Ye, Sohee Yang, Youngkyung Seo, DuSeong Chang, and Minjoon Seo. 2024. How Do Large Language Models Acquire Factual Knowledge During Pretraining? _CoRR_ abs/2406.11813 (2024).

- [7] Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde de Oliveira Pinto, Jared Kaplan, Harri Edwards, Yuri Burda, and et al. 2021. Evaluating Large Language Models Trained on Code. (2021). arXiv:2107.03374 [cs.LG]

- [8] Wei-Lin Chiang, Lianmin Zheng, Ying Sheng, Anastasios Nikolas Angelopoulos, Tianle Li, Dacheng Li, Hao Zhang, Banghua Zhu, Michael Jordan, Joseph E. Gonzalez, and Ion Stoica. 2024. Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference. arXiv:2403.04132 [cs.AI]

- [9] Guanting Dong, Hongyi Yuan, Keming Lu, Chengpeng Li, Mingfeng Xue, Dayiheng Liu, Wei Wang, Zheng Yuan, Chang Zhou, and Jingren Zhou. 2024. How Abilities in Large Language Models are Affected by Supervised Fine-tuning Data Composition. arXiv:2310.05492 [cs.CL]

- [10] Jessica Echterhoff, Yao Liu, Abeer Alessa, Julian McAuley, and Zexue He. 2024. Cognitive Bias in High-Stakes Decision-Making with LLMs. arXiv:2403.00811 [cs.AI]

- [11] Dan Hendrycks, Collin Burns, Steven Basart, Andrew Critch, Jerry Li, Dawn Song, and Jacob Steinhardt. 2021. Aligning AI With Shared Human Values. _Proceedings of the International Conference on Learning Representations (ICLR)_ (2021).

- [12] Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. 2021. Measuring Massive Multitask Language Understanding. arXiv:2009.03300 [cs.CY]

- [13] Dan Hendrycks, Collin Burns, Saurav Kadavath, Akul Arora, Steven Basart, Eric Tang, Dawn Song, and Jacob Steinhardt. 2021. Measuring Mathematical Problem Solving With the MATH Dataset. In _Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track (Round 2)_ .

- [14] Renjun Hu, Yi Cheng, Libin Meng, Jiaxin Xia, Yi Zong, Xing Shi, and Wei Lin. 2025. Training an LLM-as-a-Judge Model: Pipeline, Insights, and Practical Lessons. arXiv:2502.02988 [cs.CL]

- [15] Yuzhen Huang, Yuzhuo Bai, Zhihao Zhu, Junlei Zhang, Jinghan Zhang, Tangjun Su, Junteng Liu, Chuancheng Lv, Yikai Zhang, Jiayi Lei, Yao Fu, Maosong Sun, and Junxian He. 2023. C-Eval: A Multi-Level Multi-Discipline Chinese Evaluation Suite for Foundation Models. arXiv:2305.08322 [cs.CL]

- [16] Frederick Jelinek, Robert L. Mercer, Lalit R. Bahl, and Janet M. Baker. 1977. Perplexity—a measure of the difficulty of speech recognition tasks. _Journal of the Acoustical Society of America_ 62 (1977).

- [17] Han Jiang, Xiaoyuan Yi, Zhihua Wei, Shu Wang, and Xing Xie. 2024. Raising the Bar: Investigating the Values of Large Language Models via Generative Evolving Testing. arXiv:2406.14230 [cs.CL]

- [18] Liwei Jiang, Jena D. Hwang, Chandra Bhagavatula, Ronan Le Bras, Jenny Liang, Jesse Dodge, Keisuke Sakaguchi, Maxwell Forbes, Jon Borchardt, Saadia Gabriel, Yulia Tsvetkov, Oren Etzioni, Maarten Sap, Regina Rini, and Yejin Choi. 2022. Can Machines Learn Morality? The Delphi Experiment. arXiv:2110.07574 [cs.CL]

- [19] Pei Ke, Bosi Wen, Zhuoer Feng, Xiao Liu, Xuanyu Lei, Jiale Cheng, Shengyuan Wang, Aohan Zeng, Yuxiao Dong, Hongning Wang, Jie Tang, and Minlie Huang. 2024. CritiqueLLM: Towards an Informative Critique Generation Model for Evaluation of Large Language Model Generation. arXiv:2311.18702 [cs.CL]

- [20] Jiatong Li, Renjun Hu, Kunzhe Huang, Yan Zhuang, Qi Liu, Mengxiao Zhu, Xing Shi, and Wei Lin. 2024. PertEval: Unveiling Real Knowledge Capacity of LLMs with Knowledge-Invariant Perturbations. In _The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track_ .

- [21] Junlong Li, Shichao Sun, Weizhe Yuan, Run-Ze Fan, Hai Zhao, and Pengfei Liu. 2023. Generative Judge for Evaluating Alignment. _arXiv preprint arXiv:2310.05470_ (2023).

- [22] Ming Li, Yong Zhang, Zhitao Li, Jiuhai Chen, Lichang Chen, Ning Cheng, Jianzong Wang, Tianyi Zhou, and Jing Xiao. 2024. From Quantity to Quality: Boosting LLM Performance with Self-Guided Data Selection for Instruction Tuning.

arXiv:2308.12032 [cs.CL]

- [23] Tianle Li, Wei-Lin Chiang, Evan Frick, Lisa Dunlap, Tianhao Wu, Banghua Zhu, Joseph E. Gonzalez, and Ion Stoica. 2024. From Crowdsourced Data to High-Quality Benchmarks: Arena-Hard and BenchBuilder Pipeline. arXiv:2406.11939 [cs.LG]

- [24] Bill Yuchen Lin, Yuntian Deng, Khyathi Chandu, Faeze Brahman, Abhilasha Ravichander, Valentina Pyatkin, Nouha Dziri, Ronan Le Bras, and Yejin Choi. 2024. WildBench: Benchmarking LLMs with Challenging Tasks from Real Users in the Wild. arXiv:2406.04770 [cs.CL]

- [25] Bill Yuchen Lin, Abhilasha Ravichander, Ximing Lu, Nouha Dziri, Melanie Sclar, Khyathi Chandu, Chandra Bhagavatula, and Yejin Choi. 2024. The Unlocking Spell on Base LLMs: Rethinking Alignment via In-Context Learning. In _The Twelfth International Conference on Learning Representations_ .

- [26] Chin-Yew Lin. 2004. ROUGE: A Package for Automatic Evaluation of Summaries. In _Annual Meeting of the Association for Computational Linguistics_ .

- [27] Xiao Liu, Xuanyu Lei, Shengyuan Wang, Yue Huang, Zhuoer Feng, Bosi Wen, Jiale Cheng, Pei Ke, Yifan Xu, Weng Lam Tam, Xiaohan Zhang, Lichao Sun, Hongning Wang, Jing Zhang, Minlie Huang, Yuxiao Dong, and Jie Tang. 2023. AlignBench: Benchmarking Chinese Alignment of Large Language Models. arXiv:2311.18743 [cs.CL]

- [28] Seyed Mahed Mousavi, Simone Alghisi, and Giuseppe Riccardi. 2024. DyKnow:Dynamically Verifying Time-Sensitive Factual Knowledge in LLMs. arXiv:2404.08700 [cs.CL]

- [29] Subhabrata Mukherjee, Arindam Mitra, Ganesh Jawahar, Sahaj Agarwal, Hamid Palangi, and Ahmed Awadallah. 2023. Orca: Progressive Learning from Complex Explanation Traces of GPT-4. arXiv:2306.02707 [cs.CL]

- [30] OpenAI. 2024. GPT-4 Technical Report. arXiv:2303.08774 [cs.CL]

- [31] Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, John Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul Christiano, Jan Leike, and Ryan Lowe. 2022. Training language models to follow instructions with human feedback. arXiv:2203.02155 [cs.CL]

- [32] Oded Ovadia, Menachem Brief, Moshik Mishaeli, and Oren Elisha. 2023. Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs. _CoRR_ abs/2312.05934 (2023).

- [33] Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. 2002. Bleu: a Method for Automatic Evaluation of Machine Translation. In _Proceedings of the 40th Annual Meeting of the Association for Computational Linguistics, July 6-12, 2002, Philadelphia, PA, USA_ . ACL, 311–318.

- [34] C.A.I. Peng, Xi Yang, Aokun Chen, Kaleb E. Smith, Nima M. Pournejatian, Anthony B Costa, Cheryl Martin, Mona G. Flores, Ying Zhang, Tanja Magoc, Gloria P. Lipori, Duane A. Mitchell, Naykky Singh Ospina, Mustafa Mamon Ahmed, William R. Hogan, Elizabeth A. Shenkman, Yi Guo, Jiang Bian, and Yonghui Wu. 2023. A study of generative large language model for medical research and healthcare. _NPJ Digital Medicine_ 6 (2023).

- [35] Samyam Rajbhandari, Jeff Rasley, Olatunji Ruwase, and Yuxiong He. 2020. ZeRO: memory optimizations toward training trillion parameter models. In _Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, SC 2020, Virtual Event / Atlanta, Georgia, USA, November 9-19, 2020_ . 20.

- [36] Rylan Schaeffer, Brando Miranda, and Sanmi Koyejo. 2023. Are Emergent Abilities of Large Language Models a Mirage?. In _Advances in Neural Information Processing Systems 36: Annual Conference on Neural Information Processing Systems 2023, NeurIPS 2023, New Orleans, LA, USA, December 10 - 16, 2023_ .

- [37] Nino Scherrer, Claudia Shi, Amir Feder, and David Blei. 2023. Evaluating the Moral Beliefs Encoded in LLMs. In _Thirty-seventh Conference on Neural Information Processing Systems_ .

- [38] Ilan S Schwartz, Katherine E. Link, Roxana Daneshjou, and Nicolás W CortésPenfield. 2023. Black Box Warning: Large Language Models and the Future of Infectious Diseases Consultation. _Clinical Infectious Diseases: An Official Publication of the Infectious Diseases Society of America_ 78 (2023), 860 – 866.

- [39] Yunfan Shao, Linyang Li, Zhaoye Fei, Hang Yan, Dahua Lin, and Xipeng Qiu. 2024. Balanced Data Sampling for Language Model Training with Clustering. arXiv:2402.14526 [cs.CL]

- [40] Lichao Sun, Yue Huang, Haoran Wang, Siyuan Wu, Qihui Zhang, Yuan Li, Chujie Gao, Yixin Huang, and et al. 2024. TrustLLM: Trustworthiness in Large Language Models. arXiv:2401.05561 [cs.CL]

- [41] Rohan Taori, Ishaan Gulrajani, Tianyi Zhang, Yann Dubois, Xuechen Li, Carlos Guestrin, Percy Liang, and Tatsunori B. Hashimoto. 2023. Stanford Alpaca: An Instruction-following LLaMA model. https://github.com/tatsu-lab/stanford_ alpaca.

- [42] Gemini Team. 2024. Gemini: A Family of Highly Capable Multimodal Models. arXiv:2312.11805 [cs.CL]

- [43] Qwen Team. 2024. Qwen2 Technical Report. arXiv:2407.10671 [cs.CL]

- [44] Tu Vu, Kalpesh Krishna, Salaheddin Alzubi, Chris Tar, Manaal Faruqui, and YunHsuan Sung. 2024. Foundational Autoraters: Taming Large Language Models for Better Automatic Evaluation. arXiv:2407.10817 [cs.CL]


------------------------- PAGINA 10 --------------------------

- [45] Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A. Smith, Daniel Khashabi, and Hannaneh Hajishirzi. 2023. Self-Instruct: Aligning Language Models with Self-Generated Instructions. arXiv:2212.10560 [cs.CL]

- [46] Dongjie Yang, Ruifeng Yuan, Yuantao Fan, Yifei Yang, Zili Wang, Shusen Wang, and Hai Zhao. 2023. RefGPT: Dialogue Generation of GPT, by GPT, and for GPT. In _Findings of the Association for Computational Linguistics: EMNLP 2023, Singapore, December 6-10, 2023_ . 2511–2535.

- [47] Yu Yang, Siddhartha Mishra, Jeffrey N Chiang, and Baharan Mirzasoleiman. 2024. SmallToLarge (S2L): Scalable Data Selection for Fine-tuning Large Language Models by Summarizing Training Trajectories of Small Models. arXiv:2403.07384 [cs.CL]

- [48] Jiasheng Ye, Peiju Liu, Tianxiang Sun, Yunhua Zhou, Jun Zhan, and Xipeng Qiu. 2024. Data Mixing Laws: Optimizing Data Mixtures by Predicting Language Modeling Performance. arXiv:2403.16952 [cs.CL]

- [49] Rowan Zellers, Ari Holtzman, Yonatan Bisk, Ali Farhadi, and Yejin Choi. 2019. HellaSwag: Can a Machine Really Finish Your Sentence?. In _Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics_ .

- [50] Yunpu Zhao, Rui Zhang, Wenyi Li, Di Huang, Jiaming Guo, Shaohui Peng, Yifan Hao, Yuanbo Wen, Xing Hu, Zidong Du, Qi Guo, Ling Li, and Yunji Chen. 2024. Assessing and Understanding Creativity in Large Language Models. arXiv:2401.12491 [cs.CL]

- [51] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Tianle Li, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zhuohan Li, Zi Lin, Eric P. Xing, Joseph E. Gonzalez, Ion Stoica, and Hao Zhang. 2024. LMSYS-Chat-1M: A Large-Scale Real-World LLM Conversation Dataset. arXiv:2309.11998 [cs.CL]

- [52] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. 2023. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. In _Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track_ .

- [53] Wanjun Zhong, Ruixiang Cui, Yiduo Guo, Yaobo Liang, Shuai Lu, Yanlin Wang, Amin Saied, Weizhu Chen, and Nan Duan. 2023. AGIEval: A Human-Centric Benchmark for Evaluating Foundation Models. arXiv:2304.06364 [cs.CL]

- [54] Kun Zhou, Yutao Zhu, Zhipeng Chen, Wentong Chen, Wayne Xin Zhao, Xu Chen, Yankai Lin, Ji-Rong Wen, and Jiawei Han. 2023. Don’t Make Your LLM an Evaluation Benchmark Cheater. arXiv:2311.01964 [cs.CL]

## **A Detailed Scenarios**

In this section, we detail the ten scenarios currently supported by Themis as well as their descriptions. Due to space constraint, judge criteria are left to an extended version of this paper [14].

**Question-answer Scenarios** . <u>(1) Close QA.</u> Solve a problem that may involve professional knowledge or real-world inquiries, such as historical facts or scientific laws, and the problem has a standard/reference answer. <u>(2) Open QA.</u> Open dialogue instructions, usually asking an open-field question, and responses are also open-ended, such as casual chats, advice consultations, recommendations, etc. <u>(3) Math-related QA. Solve a problem involving</u> mathematics, calculations, reasoning, etc., and the problem has a standard/reference answer.

**Writing scenarios** . <u>(4) Creative writing. Writing that primarily</u> expresses personalized imagination and emotions, focusing on literary quality and originality, such as creating essays, poems, lyrics, scripts, stories, speeches, social media posts, blogs, advertising materials, brainstorming, etc. <u>(5) Informative and professional writing.</u> Writing aimed at conveying key information and professional knowledge, focusing on accuracy, reliability, and authority, covering practical emails, job applications, product descriptions, user manuals, to in-depth academic papers, medical research, legal opinions, engineering design, industry analysis, economic forecasts, and other complex documents. <u>(6) Rewriting. Includes text simplification, lan-</u> guage optimization, rewriting text according to instructions, text correction, text summarization and expansion, etc.

**Professional scenarios** . <u>(7) Translation.</u> Translate the given text into another language without changing the original meaning. <u>(8) Reading comprehension and extraction. Read materials and com-</u> plete directive tasks based on the materials, such as Q&A, summarization, keyword extraction, topic extraction, title generation, fact-checking, etc. <u>(9) Role-playing. Pretend to be a particular per-</u> son, character, profession, or identity, and complete the tasks in the instructions based on this role. <u>(10) Programming-related.</u> Tasks related to computer code, including implementing code based on requirements, code modification and optimization, programming language conversion, analyzing code and responding to related questions, software development assistance, etc.

**Table 5: Scenario mapping between Themis and Llama-3**

|**Themis scenarios**|**Llama-3 use cases**|
|---|---|
|(1*) Closed-QA|(1) Closed question answering|
|(2*) Open-QA|(2) Open question answering<br>(3) Asking for advice<br>(4) Brainstorming|
|(3) Math-related QA|(5) Reasoning|
|(4*) Creative writing|(6) Creative writing|
|(5) Info. and prof. writing|NA|
|(6*) Rewriting|(7) Rewriting|
|(7) Translation|NA|
|(8*) Reading compre. and extrac.|(8) Extraction<br>(9) Summarization|
|(9*) Role-playing|(10) Inhabiting a character|
|(10*) Programming-related|(11) Coding|
|NA|(12) Classification|

**Justification for scenario design** . Table 5 illustrates the mapping between Themis’s scenarios and Llama-3’s evaluation use cases [1]. From the table we can see that 7 out of Themis’s 10 scenarios, _i.e.,_ those with *, have direct mapping to the ones of Llama-3. The remaining math-related QA, informative and professional writing, and translation are popular applications of LLMs and deserve context-specific evaluations. On the other side, 11 out of Llama-3’s 12 use cases, except for classification, are covered by Themis. As the scenario design of Themis is independent with Llama-3, the above comparison could be regarded as an empirical justification for our scenario design through human-AI collaboration.

## **B Prompts**

In addition to Table 1, extra prompts related to Themis training and inference include the ones for reference-guided grading, pairwise comparison, reference-based question synthesis, role-playing quizzing for three scenarios, and fine-tuning the scenario classification LLM. Please refer to [14] for all these prompts, as well as a complete evaluation record for supervised fine-tuning and evaluation results by different judge models.
