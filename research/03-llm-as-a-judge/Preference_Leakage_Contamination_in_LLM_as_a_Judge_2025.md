# Preference Leakage: A Contamination Problem in LLM-as-a-judge

> **En [`docs/pvb.md`](../../docs/pvb.md): `[7]`** · **En [`docs/critica.md`](../../docs/critica.md): `[3]`**  
> Li, D., Sun, R., Huang, Y., Zhong, M., Jiang, B., Han, J., Zhang, X., Wang, W., & Liu, H. (2025). *Preference Leakage: A Contamination Problem in LLM-as-a-judge*. arXiv preprint arXiv:2502.01534.  
> 
> Secciones de `pvb.md`: 1. PROBLEMA · 5. UX PARADIGM  
> Secciones de `critica.md`: Riesgo 2: Engaño por instrucciones habladas (Spoken Prompt Injection)  
> Fuente convertida: `1-papersMD/0-Base_propuesta/Preference_Leakage_Contamination_in_LLM_as_a_Judge_2025.md`


**Archivo origen:** `1-papers/0-Base_propuesta/2502.01534v2.pdf`  
**Páginas:** 20  
**Nota:** los separadores `PAGINA n` corresponden a la página física del PDF. Los encabezados y pies de página repetidos se conservan solo en su primera aparición.


------------------------- PAGINA 1 --------------------------

# **_Preference Leakage_ : A Contamination Problem in LLM-as-a-judge**

**Dawei Li**<sup>_∗_1</sup> **, Renliang Sun**<sup>_∗_2</sup> **, Yue Huang**<sup>3</sup> **, Ming Zhong**<sup>4</sup> **, Bohan Jiang**<sup>1</sup> , **Jiawei Han**<sup>4</sup> , **Xiangliang Zhang**<sup>3</sup> , **Wei Wang**<sup>2</sup> , **Huan Liu**<sup>1</sup> 1Arizona State University, 2University of California, Los Angeles,

3University of Notre Dame, 4University of Illinois Urbana-Champaign daweili5@asu.edu

## **Abstract**

Large Language Models (LLMs) as judges and LLM-based data synthesis have emerged as two fundamental LLM-driven data annotation methods in model development. While their combination significantly enhances the efficiency of model training and evaluation, little attention has been given to the potential contamination brought by this new model development paradigm. In this work, we expose preference leakage, a contamination problem in LLM-as-a-judge caused by the relatedness between the synthetic data generators and LLM-based evaluators. To study this issue, we first define three common relatednesses between the data generator LLM and the judge LLM: being the same model, having an inheritance relationship, and belonging to the same model family. Through extensive experiments, we empirically confirm the bias of judges towards their related student models caused by preference leakage across multiple LLM baselines and benchmarks. Further analysis suggests that preference leakage is a pervasive and real-world problem that is harder to detect compared to previously identified biases in LLM-as-a-judge scenarios. All of these findings imply that preference leakage is a widespread and challenging problem in the area of LLM-as-a-judge. We release all codes and data at: https://github.com/David-Li0406/Preference-Leakage<sup>2</sup> .

## **1 Introduction**

Recent advancements in Large Language Models (LLMs) [1, 22, 60, 74] have empowered various downstream tasks and applications. However, this also poses substantial challenges to the automatic evaluation of these models. Representatively, LLM-based AI agents’ focus transfer from traditional natural language processing tasks [70, 73] to real-world [46, 20], open-ended response generation [65], which greatly limits the applicability of traditional n-gram matching methods (e.g., BLEU [50] and ROUGE [41]) [43, 53] or model-based evaluators [77, 81] for evaluation.

To address these challenges, the paradigm of LLM-as-a-judge [79, 34, 24, 82, 37] has been proposed, designed to leverage LLM as evaluators to assess response quality. By combining powerful LLMs with well-designed prompting strategies, LLM-as-a-judge enables human-like evaluation of long-form and open-ended generation in a more cost-efficient and scalable manner. However, recent studies point out some weaknesses of such an assessment. For instance, Ye et al. [72] explores various biases and vulnerabilities of LLM-as-a-judge, highlighting the importance of developing a reliable and fair LLM-based evaluation system.

> _∗_ Equal contribution.

> 2More resources on LLM-as-a-judge are on the website: https://llm-as-a-judge.github.io/

Preprint. Under review.


------------------------- PAGINA 2 --------------------------

<!-- Start of picture text -->
Data leakage Data Leakage! (1). Same model<br>Train Evaluate<br>Training Trained Evaluation  Trained (2). Inheritance<br>Corpus Model Testset Model<br>Training Evaluation<br>Corpus Testset Overlap<br>Synthetic<br>data<br>Preference leakage Preference Leakage!<br>Synthesize Train Judge<br>(3). Within the<br>Data  Synthetic  Trained Judge same model family<br>Generator Data Model Model<br>LLM for Data  LLM-as-<br>Synthesis a-Judge Relatedness<br><!-- End of picture text -->

Figure 1: Overview of preference leakage. We make a comparison between data leakage and preference leakage and present three types of relatedness: being the same model, having an inheritance relationship and belonging to the same model family.

In this work, we aim to highlight a subtle yet critical bias in LLM-as-a-Judge: _Preference Leakage_ . This issue arises when _the LLMs used for data generation and evaluation are closely related, causing the preference of the LLM evaluators to leak to the student models through synthetic data and thus inflating the evaluation score_ (as illustrated in Figure 1). Synthetic data generated by LLMs [15, 57, 35, 36] has become a cornerstone of model training [32]. When combined with LLM-as-a-Judge, they offer significant efficiency gains in model development. However, limited attention has been given to the potential contamination that occurs when the generator and evaluator LLMs share a close relationship. During our preliminary study, we find this issue is particularly pervasive in popular LLM-as-a-judge benchmarks (e.g., AlpacaEval 2.0 [14] and Arena-Hard [39]) and LLM-relevant studies (more details can be found in Appendix A), due to the common reliance on the most advanced LLMs, such as GPT-4 [1], for both data synthesis and evaluation to ensure the highest quality outputs. In our work, we reveal this relatedness—akin to the overlap between training data and evaluation sets in traditional data contamination—would introduce a systematic bias of judge LLMs towards their related student models (i.e., the model distilled by the data generator which is related to the judge). Compared to other biases in LLM-as-a-Judge, such as length bias or egocentric bias [72, 49], preference leakage is subtler and more challenging to detect, especially given that most LLMs do not disclose their training data.

To investigate and reveal the preference leakage problem, we first define three relatednesses between data generator LLM and judge LLM: being the same model, having an inheritance relationship, and belonging to the same model family. Each of these scenarios is commonly encountered in real-world applications. Then, we pose and answer three core research questions about preference leakage:

- **RQ1: Does preference leakage introduce systematic biases in LLM-based evaluation?** To answer it, we conduct experiments with various LLM baselines in two widely recognized LLM-asa-judge benchmarks, also introduce the preference leakage score to quantify the bias caused by preference leakage. The analysis results suggest an obvious bias of judging LLMs toward their related student models due to preference leakage.

- **RQ2: What is the severity of preference leakage under various scenarios?** We conduct experiments under various data mixing strategies, relatedness settings, tuning techniques and real-world applications to address it, finding that preference leakage consistently affects judge LLMs. Moreover, the severity of preference leakage correlates with the degree of relatedness between the data generator and LLM judges, as well as the proportion of synthetic data.

- **RQ3: What are the underlying mechanisms causing preference leakage?** For this question, we analyze LLMs’ recognition capabilities on their related student models’ generation as well as the distribution of bias across different question types and judgment dimensions. The analysis reveals that preference leakage is a subtle, hard-to-detect issue for the LLM evaluators, particularly affecting subjective questions and judgment dimensions.

To summarize, our contributions in this work are as follows:

- For the first time, we introduce preference leakage, a contamination issue arising from the relatedness between the data generator and judge LLMs.

- We conduct extensive experiments across various LLMs and benchmarks to study how and to what extent the potential bias brought by preference leakage influences judgment.


------------------------- PAGINA 3 --------------------------

- Our further analysis reveals that preference leakage is prevalent in diverse scenarios and difficult for judge LLMs to detect, providing valuable insights for future research on this challenging issue.

## **2 Related Work**

**LLM-as-a-Judge.** LLM-as-a-Judge, introduced by Zheng et al. [79], leverages LLMs to automatically evaluate responses and assign rewards. This approach has gained widespread adoption in areas such as model alignment [78] and benchmarking [45, 75, 16, 82], driving significant progress in the field. Building on this concept, Zhuge et al. [84] proposed Agent-as-a-Judge, where agentic systems are employed to evaluate other agentic systems. Additionally, Prometheus, a series of open-source LLMs tailored for LLM-as-a-Judge [26, 27], addresses the prohibitive costs associated with proprietary models, further democratizing the technology.

Despite its promising potential, recent studies have highlighted the vulnerabilities and biases of LLM-as-a-Judge [79, 72, 28, 4, 79, 21, 59, 54]. Among these, egocentric bias, where LLM evaluators tend to favor their generations [29, 47, 63, 68, 52, 49, 5], is most closely related to the preference leakage proposed in this work.

However, in contrast to the relatively straightforward setting of egocentric bias, preference leakage presents a more complex and dynamic challenge. It can arise from various types of relatedness between data-generating and evaluating LLMs, as well as the intricate flow of synthetic data among modern LLMs [57]. Moreover, detecting preference leakage is also more challenging, given LLMs often do not disclose their training data and the difficulty in distillation quantification [61, 32].

**Data Leakage.** The possible overlap between training data and evaluation benchmarks has become a central issue, since LLMs are usually trained on extensive web corpora [9]. This phenomenon, known as data leakage, can artificially improve the performance of LLMs and undermine the reliability of the assessment [7, 25]. Several researchers have proposed methods to detect and mitigate data contamination. Deng et al. [8] proposed a retrieval-based approach to assess the degree of overlap between pre-training text and benchmark data. Golchin and Surdeanu [17] have developed “guided instruction” to flag contaminated instances. Dong et al. [11] proposed the CDD method to identify peaks in the output distribution to detect data contamination. Several studies analyze data leakage for specific LLMs [2, 67] and report contamination such as cross-language contamination [71] and task contamination [33] that can evade traditional detection methods. To address data contamination issues, Ni et al. [48] have used web user query detection and benchmark mixture. White et al. [64] use the most recent information to update the problem.

## **3 Preference Leakage**

### **3.1 LLMs as Oracles: A New Avenue for Contamination**

With the advent of LLMs, these models are increasingly employed as “oracles” in various scenarios: for both synthetic data generation ( _MG_ ) and employed as evaluators ( _MJ_ ) to automate the assessment. While these approaches enhance scalability and efficiency, they also introduce potential risks. Specifically, if the LLM used for data generation ( _MG_ ) and the LLM used for evaluation ( _MJ_ ) are not independent, a new contamination—preference leakage—can emerge, biasing evaluation outcomes.

### **3.2 Defining Preference Leakage in LLM-based Evaluation**

Formally, to define preference leakage, we consider the following entities in models development:

- **Data Generator LLM,** _MG_ , defining a conditional distribution _PMG_ ( _y|x_ ) for generating an output _y_ given a prompt _x_ , forming the synthetic dataset _Dsyn_ for student LLMs training.

- **Student LLM,** _MS_ , trained on data generated by _MG_ , producing an output distribution _PMS_ ( _y|x_ ).

- **Judge LLM,** _MJ_ , providing a scoring function _SMJ_ ( _y|x_ ) that assesses output _y_ for prompt _x_ .

Preference leakage occurs when the evaluation score assigned by _MJ_ to _MS_ ’s outputs is inflated due to an underlying relatedness between _MG_ and _MJ_ . This implies that _MJ_ may favor outputs from _MS_ not solely based on their intrinsic quality, but because they exhibit spurious features (e.g., style, format, wording) inherited from _MG_ , to which _MJ_ is predisposed due to this relatedness:


------------------------- PAGINA 4 --------------------------

where _yS_ are outputs from _MS_ . The relation _MG ∼rel MJ_ denotes that judge _MJ_ is related to _MG_ , while _MG̸ ∼rel MJ ′_ denotes that an alternative judge _MJ ′_ is not related to _MG_ and possess comparable intrinsic quality assessment capabilities to _MJ_ . The expectation is taken over the input distribution _X_ and the trained Student LLM’s output distribution _PMS_ .

### **3.3 Type of LLM “Relatedness”**

The condition _MG ∼rel MJ_ in Equation 1 encapsulates several ways the Data Generator LLM and Judge LLM can be interconnected. We identify three common types in the real world:

- **Being the Same Model:** The most direct form of relatedness occurs when the Data Generator LLM and the Judge LLM are the exact same model instance:

- In this scenario, the inherent preferences in the model that shape its generative distribution _PMG_ ( _y|x_ ) are precisely the same as those guiding its evaluation via the scoring function _SMG_ ( _y|x_ ).

- **Inheritance Relationship:** One model’s development is directly based on another, either by fine-tuning the existing model or by training a new model on the other’s outputs, for instance:

where _Dtrain_ represents general training data used to adapt _MG_ into _MJ_ , _Mbase_ is a base model, and _DsynG_ denotes synthetic data generated by _MG_ . This type of relationship is bidirectional; _MG_ can similarly inherit from _MJ_ through analogous processes. In such cases, the descendant model is likely to internalize and thus favor the preferences, styles, or biases of its progenitor.

- **Within the Same Model Family:** The Data Generator LLM _MG_ and Judge LLM _MJ_ belong to the same model family (e.g., different versions or sizes of GPT). Models within such a family typically share a common architectural blueprint ( _AX_ ) and are often developed from foundational models pre-trained on substantially overlapping datasets ( _DX_ ). This shared foundation ( _AX , DX_ ) would lead to correlated preferences and systemic biases characteristic of the common origin:

## **4 Main Experiment**

<!-- Start of picture text -->
Mistral-GPT4o vs Mistral-Gemini-1.5 Mistral-GPT4o vs Mistral-LLaMA-3.3 Mistral-LLaMA-3.3 vs Mistral-Gemini-1.5<br>GPT-4o 38.4% 34.6% 27.0% 55.8% 27.0% 17.2% 22.2% 30.8% 47.0%<br>LLaMA-3.3 27.4% 43.8% 28.8% 50.4% 35.0% 14.6% 14.6% 30.0% 55.4%<br>Gemini-1.5 18.2% 39.8% 42.0% 46.2% 42.7% 11.1% 9.2% 31.4% 59.4%<br>0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0%<br>(a). Mistral-7B<br>Qwen-GPT4o vs Qwen-Gemini-1.5 Qwen-GPT4o vs Qwen-LLaMA-3.3 Qwen-LLaMA-3.3 vs Qwen-Gemini-1.5<br>GPT-4o 49.8% 29.0% 21.2% 57.4% 29.6% 13.0% 24.6% 30.0% 44.4%<br>LLaMA-3.3 28.8% 50.2% 21.6% 39.0% 51.8% 9.2% 16.4% 48.4% 35.2%<br>Gemini-1.5 22.0% 33.5% 44.5% 52.1% 40.7% 7.2% 1 0.0% 29.4% 60.6%<br>0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0%<br>(b). Qwen-2.5-14B<br>Model A Wins Tie Model B Wins<br>Judge Model<br><!-- End of picture text -->

Figure 2: Judgment results with GPT-4o, LLaMA-3.3 and Gemini-1.5 on Arena-Hard.

### **4.1 Experiment Setup**

**Models.** We choose three powerful LLMs as data generator/ judge models. They are GPT-4o-202411-20 [1], Gemini-1.5-flash [58], and LLaMA-3.3-70B-Instruct-turbo [13]. For the student model, we choose Mistral-7B-v0.1 [23] and Qwen-2.5-14B [69]. To avoid potential preference leakage


------------------------- PAGINA 5 --------------------------

due to distilling data from other LLMs during the instruction-tuning process, we choose to use the -PRE-TRAINED version rather than the -INSTRUCT version of these student models.

**Evaluation Datasets.** We choose two representative pairwise evaluation datasets, Arena-Hard [39] and AlpacaEval 2.0 [14], to evaluate the trained student models. Arena-Hard includes 500 challenging questions in English. Additionally, the evaluation agreement between Arena-Hard and Chatbot Arena [79]’s hard prompts achieved a 96.7% Spearman correlation, demonstrating the consistency of Arena-Hard with human preferences [39]. AlpacaEval 2.0 is an improved evaluation method based on AlpacaEval [40] and contains 805 questions. Compared to version 1.0, AlpacaEval 2.0 significantly reduces the effect of text length on the evaluation results.

**Implementation Details.** In our main experiment, we examine the preference leakage introduced by using the same data generator and evaluator in supervised fine-tuning (SFT). We will discuss other relatedness and learning methods in Section 5. To obtain synthetic datasets, We first randomly sample 30,000 prompts from the Ultrafeedback dataset [6]. The Ultrafeedback dataset includes instructions from several publicly available high-quality datasets such as TruthfulQA [42], FalseQA [19], and Evol-Instruct [66]. For each data generator model, we provide these prompts for them to produce synthetic responses, resulting in three synthetic instruction datasets. We then use each dataset to supervised fine-tune the student model, obtaining three different versions for each baseline: Mistral/ Qwen-GPT-4o, Mistral/ Qwen-Gemini-1.5 and Mistral/ Qwen-LLaMA-3.3. After that, we pair each two student models and obtain three model pairs. For each model pair, we perform the pairwise comparison using the three judge models respectively.

<!-- Start of picture text -->
Mistral-GPT4o vs Mistral-Gemini-1.5 Mistral-GPT4o vs Mistral-LLaMA-3.3 Mistral-LLaMA-3.3 vs Mistral-Gemini-1.5<br>GPT-4o 55.1% 44.9% 61.6% 38.4% 43.1% 56.9%<br>LLaMA-3.3 49.5% 50.5% 60.3% 39.7% 39.5% 60.5%<br>Gemini-1.5 36.8% 63.2% 65.8% 34.2% 22.6% 77.4%<br>0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0%<br>(a). Mistral-7B<br>Qwen-GPT4o vs Qwen-Gemini-1.5 Qwen-GPT4o vs Qwen-LLaMA-3.3 Qwen-LLaMA-3.3 vs Qwen-Gemini-1.5<br>GPT-4o 57.8% 42.2% 61.5% 38.5% 50.1% 49.9%<br>LLaMA-3.3 52.4% 47.6% 59.3% 40.7% 42.9% 57.1%<br>Gemini-1.5 39.3% 60.7% 63.3% 36.7% 26.2% 73.8%<br>0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0%<br>(b). Qwen-2.5-14B<br>Model A Wins Model B Wins<br>Judge Model<br><!-- End of picture text -->

Figure 3: Judgment results with GPT-4o, LLaMA-3.3 and Gemini-1.5 on AlpacaEval 2.0. Different from Arena-Hard, there is no tie in AlpacaEval 2.0.

**Metrics** Based on our hypothesis, preference leakage would lead to bias of judge LLMs towards their related student models. Following this principle, we design the preference leakage score PLS( _i, j_ ) to measure the bias in model pair ( _i, j_ ) caused by preference leakage:

Here WR( _i, j_ ) represents the win-rate score from judge model _j_ to student model _i_ . Intuitively, a large preference leakage score indicates that the two judge models demonstrate strong bias toward their related student models, suggesting a significant preference leakage phenomenon.

More details about model training and metric explanation can be found in Appendix B.

### **4.2 Main Results**

In our main experiment, we aim to provide insights into RQ1.

**Preference leakage exists in most model pairs.** The original judgment results from Arena-Hard and AlpacaEval 2.0, along with the calculated preference leakage scores, are shown in Figure 2, Figure 3, and Table 1. As the results demonstrate, in most model pairs (except Mistral-GPT-4o vs Mistral-LLaMA-3.3 and Qwen-GPT-4o vs Qwen-LLaMA-3.3), the judge LLMs exhibit a strong


------------------------- PAGINA 6 --------------------------

Table 1: Preference leakage score result on Arena-Hard and AlpacaEval 2.0. The <mark>blue</mark> background indicates a negative preference leakage score value and the <mark>purple</mark> background indicates a positive value. The deeper the color, the larger the absolute value.

|**Model**|**Data Generator/ Judge Pair**|**Arena-Hard**|**AlpacaEval 2.0**|**Avg.**|
|---|---|---|---|---|
||GPT-4o & Gemini-1.5|28.7%|18.4%|23.6%|
|Mistral-7B|GPT-4o & LLaMA-3.3|-1.5%|1.4%|-0.1%|
||LLaMA-3.3 & Gemini-1.5|13.1%|19.8%|16.4%|
||GPT-4o & Gemini-1.5|37.1%|18.6%|27.9%|
|Qwen-2.5-14B|GPT-4o & LLaMA-3.3|1.0%|2.3%|1.7%|
||LLaMA-3.3 & Gemini-1.5|25.4%|18.4%|21.9%|

preference toward their related student models, leading to large positive values in the preference leakage scores. This finding suggests that preference leakage, along with the resulting bias, is widespread in SFT when the data generator and evaluator are the same.

**Smaller student models cause even more bias from judge LLMs.** To investigate the impact of student model size on the degree of preference leakage, we conduct additional experiments using various sizes of the Qwen-2.5 and Qwen-3 models. As shown in Figure 4.2 (a), a notable finding is that the smallest models (Qwen-2.5-3B and Qwen-3-1.7B) exhibit the highest PL scores than their larger counterparts, indicating greater bias from preference leakage. This trend contrasts with the influence of model size in data contamination, where larger models are typically more susceptible [3]. We assume that this gap arises from the differing learning capabilities and behaviors of large and small LLMs: while larger models are more prone to memorizing [12] information that exacerbates data contamination. Compared with them, smaller models may only be able to learn those spurious features that repeatedly occurs (e.g., format), leading to more serious preference leakage.

**Different benchmarks result in varying degrees of bias under preference leakage.** Another observation from Table 1 and Figure 4.2 (a) is that the PL scores in ArenaHard are generally higher than those in AlpacaEval 2.0. One possible explanation is the difference in question difficulty between the two benchmarks, as ArenaHard contains more challenging questions. Additionally, it may also stem from differences in the distribution of question types, the impact of which on preference leakage will be further analyzed in Section 5.6.

<!-- Start of picture text -->
50 AlpacaEval 2.0<br>ArenaHard<br>40<br>30<br>20<br>10<br>0<br>Qwen-2.5-3BQwen-2.5-7BQwen-2.5-14BQwen-3-1.7BQwen-3-4BQwen-3-8BQwen-3-14B<br>PL Score<br><!-- End of picture text -->

(a) PLS on models with various sizes. We conduct the experiment with GPT-4o and Gemini as data generators and judges.

<!-- Start of picture text -->
30<br>25<br>20<br>15<br>10<br>AlpacaEval2.0 - Manual<br>5 ArenaHard - Manual<br>AlpacaEval2.0 - Synthetic<br>0 ArenaHard - Synthetic<br>20 40 60 80 100<br>Contamination Ratio (%)<br>Preference Leakage Score (%)<br><!-- End of picture text -->

<!-- Start of picture text -->
(b) Experiment results on data mixing. ‘Manual’ and<br>‘Synthetic represent mixing with manually-written data<br>and other synthetic data, respectively.<br><!-- End of picture text -->

Figure 4: Experiment results on additional models and data mixing settings.

## **5 Further Analysis**

In this section, we conduct data mixing analysis, relatedness analysis, learning method analysis, and real-world impact analysis (Section 5.1 - 5.4) to answer RQ2. Due to the cost consideration, we conduct these analyses on Mistral-GPT-4o vs Mistral-Gemini-1.5. Moreover, we perform recognition analysis and category analysis to answer RQ3.


------------------------- PAGINA 7 --------------------------

### **5.1 Data Mixing Analysis**

In real-world applications, synthetic data from a single LLM is often mixed with manually-written data or other multi-source synthetic data to train student models. To mimic these scenarios and explore how much synthetic data could lead to preference leakage, we conduct a data mixing analysis. Specifically, we randomly sample 10%, 30%, 50%, and 70% from the original synthetic dataset and mix it with manually-written data and multi-source synthetic data, respectively, in order to maintain a consistent total volume of training data (30,000). For the manually-written data, we sample from the data pool collected in Section 5.3. For the multi-source synthetic data, we use the original synthetic data from Ultrafeedback, which includes responses generated by various LLMs (e.g., WizardLM, Flcon, etc.). After obtaining the mixing training data, we train the student models using SFT and calculate their preference leakage scores based on the judgment results. Figure 4.2 (b) presents the results with two mixing strategies across two benchmarks.

**The degree of preference leakage is directly proportional to the amount of synthetic data.** We observe a strong correlation between the proportion of synthetic data in the mixture and the preference leakage score, with no clear threshold separating cases with preference leakage from those without. This suggests that preference leakage can occur even with a small amount of leaked synthetic data, posing significant challenges for its detection.

### **5.2 Relatedness Analysis**

We demonstrate the impact of different relatedness conditions between the data generator and the judge LLM on the preference leakage problem, as shown in Table 2.

**Preference leakage under inheritance settings causes obvious bias of judges towards their related students.** For the inheritance relationship, we consider the situation where the data generator is inherited from the judge model. We conducted the following two experiments: (1). we give the same instructions again as in the SFT stage (Inheritance w/ same ins.), or (2). we sample the same number of different instruc-

Table 2: Preference leakage score in different relatedness between the data generator and the judging LLM.

||**Arena-Hard**|**AlpacaEval 2.0**|**Avg.**|
|---|---|---|---|
|Same Model|28.7%|18.4%|23.6%|
|Inheritance<br>- w/ same ins.|17.8%|20.7%|19.3%|
|Inheritance<br>- w/ different ins.|18.3%|26.3%|22.3%|
|Same Family<br>- w/ same series|10.1%|7.6%|8.9%|
|Same Family<br>- w/ different series|3.3%|2.2%|2.8%|

tions from the Ultrafeedback (Inherence w/ different ins.). Then, we let the fine-tuned Mistral model generate the answers and use these generated data to fine-tune a new Mistral student model. From the results, with the same instructions, the average preference leakage score is 19.3%. In comparison, the score with different instructions is 22.3%. Firstly, in an inheritance setting, data generators can inherit judges’ preferences, which are then passed on to new student models, thereby compromising the fairness of their evaluation. Second, even when different instructions are used, judges’ preferences leaked to data generators can still be transferred to the new student model through synthetic data, leading to a high preference leakage score.

**Models within the same series tend to cause more significant bias.** For two models within the same family, we consider two settings: (1) Same series, where training data is generated by GPT-4o and Gemini-1.5-flash, and judged by GPT-4-turbo and Gemini-1.5-pro; (2) Different series, where training data is still generated by GPT-4o and Gemini-1.5-flash, but judged by GPT-3.5-turbo and Gemini-1.0-pro. In the same series setting, the average preference leakage score is 8.9%, indicating that despite using different models for data generation and judgment, their relatedness in terms of model family leads to some preference leakage. In contrast, the different series setting yields a significantly lower leakage score of 2.8%, likely due to differences in architecture, training data, and other factors, reducing the influence of model-related biases in evaluation.

### **5.3 Learning Method Analysis**

We also compare three learning methods, supervised fine-tuning (SFT), direct preference optimization (DPO) [51], and in-context learning (ICL) [10], to explore the different influences to

Table 3: Preference leakage score in different learning methods.

|SFT|**Arena-Hard**<br>28.7%|**AlpacaEval 2.0**<br>18.4%|**Avg.**<br>23.6%|
|---|---|---|---|
|DPO|7.7%|2.7%|5.2%|
|ICL<br>7|-4.2%|-1.1%|-2.7%|


------------------------- PAGINA 8 --------------------------

them under preference leakage. We first build a data pool based on human-written instructiontuning data from OASST [30], LIMA [83], and MOSS [56] to supervised fine-tune the pretrained model. For DPO, we sample 2 responses for each instruction from sampled UltraFeedback instruction and prompt each data generator to produce the pairwise feedback. Then we use the DPO loss to further train the fine-tuned policy on each synthetic pairwise dataset. Appendix C shows the prompt we use to craft synthetic pairwise feedback. For ICL, we sample 4 instruction-response pairs from each LLMs’ synthetic dataset as the demonstration during inference.

**Tuning approaches would leak judges’ preference to the student models.** Various learning methods show significant differences in preference leakage scores across learning methods. SFT exhibits the highest average leakage score at 23.6%. In contrast, DPO achieves a much lower score of 5.2%, which is consistent with previous studies in data contamination that pairwise optimization can reduce the risk of memorizing or contaminating sensitive training data compared to straightforward supervised fine-tuning [18]. Meanwhile, ICL, which relies on contextual examples without model tuning, is least affected by the data generator’s preferences, resulting in the lowest leakage scores.

### **5.4 Real-world Impact Analysis**

Table 4: Impact analysis of preference leakage in real-world LLM-as-a-Judge leaderboards. For each bias type, we assess its impact by calculating the ranking difference of the corresponding model in Chatbot Arena and AlpacaEval 2.0, obtained by subtracting the ranking in AlpacaEval 2.0 from that in Chatbot Arena. A larger positive ranking difference indicates AlpacaEval 2.0 ranks the target models in higher positions, denoting a greater impact of the corresponding bias.

|**Bias Type**|**Evaluator**|**Target Models**<br>**Ranking Difference**|
|---|---|---|
|Egocentric Bias<br>Preference Leakage|GPT-4 Preview|GPT-4 Preview<br>1.00<br>Vicuna 7B/ 13B/ 33B<br>**1.33**|

In this section, we investigate the impact of preference leakage in real-world LLM-as-a-Judge leaderboards. We take AlpacaEval 2.0 as a case study and compare preference leakage with egocentric bias. To quantify the effect of each bias type, we calculate the ranking difference of each target model in Chatbot Arena and AlpacaEval 2.0.

As shown in Table 4, both egocentric bias and preference leakage result in a positive ranking difference, indicating that both lead to evaluator bias favoring the target models. Notably, the ranking difference associated with preference leakage is even higher than that of egocentric bias, highlighting the substantial impact of preference leakage on real-world LLM-as-a-Judge leaderboards.

### **5.5 Can Judges Recognize Student Models?**

Table 5: Student recognition (binary classification) and response classification results (three-class classification). SR: Student Recognition, RC: Response Classification.

|**Task**|**Model**|**Accu**|**racy**|
|---|---|---|---|
|||**Pointwise**|**Pairwise**|
||GPT-4o|41.0%|52.0%|
|SR|Gemini-1.5|53.2%|44.2%|
||LLaMA-3.3|41.8%|29.8%|
|RC|BERT|82.4|%|

Previous studies demonstrate the LLM judges can recognize and thus prefer their own generation [49]. In this work, we pose a similar question: _Does preference leakage also source from the LLM judges’ recognition of their related student models’ generation?_ To study this, we follow Panickssery et al. [49] to prompt the three judge LLMs and test whether they could recognize their related student models’ generation. Additionally, we split three student models’ generation into training and testing sets, and train a BERT classifier to perform a three-class classification inspired by the previous study on detecting human-AI text [76]. For student recognition, we follow Panickssery et al. [49] to use both pointwise and pairwise settings. Due to the

space limitation, more detailed prompting and training settings can be found in Appendix E.


------------------------- PAGINA 9 --------------------------

**Judge LLMs do not show good performance in recognizing the generation of their student models.** As the result presented in Table 5, we find that the recognition performance of each judge LLM in the content of related students is poor, with accuracy around the performance of random guess. This suggests that preference leakage is subtler and harder-to-detect for judge LLMs, in contrast to the more obvious egocentric bias.

**Certain features embedded in student models through synthetic data.** Although judge LLMs do not perform well in related student recognition, we notice the fine-tuned BERT classification demonstrates a high accuracy score in classifier responses generated by each student model. This suggests that certain characteristics—such as style and format—are embedded in the student models through the synthetic responses. This finding further supports the existence of preference leakage and lays the groundwork for future research aimed at detecting and preventing it.

### **5.6 Impact on Question Type & Judgment Dimension**

<!-- Start of picture text -->
31.4<br>32.4<br>30 32<br>23.8 30.2 30.4 30.7<br>21.0 28.6 28.8 29.0 29.2<br>20 16.5 17.2 17.3 28 27.9<br>10 7.7 24<br>0 20<br>(a) Question Type (b) Judgment dimension<br>MathematicsBusinessDaily Life Science Writing OthersProgramming CompletenessClarityRichnessSatisfactionFactualityLogicalOthersCreativityFairness<br>Preference Leakage Score (%) Preference Leakage Score (%)<br><!-- End of picture text -->

Figure 5: Category analysis results on question type and judgment dimension.

In this section, we explore the impact of preference leakage across various question types and judgment dimensions. For the question type analysis, we first propose several general question types based on the question clusters introduced by Arena-Hard. Then, we prompt GPT-4o to map each question in Arena-Hard and AlpacaEval to one of the question types and calculate the preference leakage score for each question category. For the judgment dimension analysis, we follow the judgment dimensions introduced by Liu et al. [45] and also utilize GPT-4o to map the rationale generated by judge LLMs to one or multiple judgment dimensions. More detailed prompt can be found in Appendix F. The analysis results are presented in Figure 5.

**Subjective question and judgment dimension tend to lead to more bias.** For question type analysis, we find objective questions with a definitive answer, like mathematical ones, demonstrate the least preference leakage. By contrast, subjective questions that have more than one standard answer, such as programming and writing, usually lead to a more obvious preference leakage. This observation is also applied to judgment dimension analysis, as objective dimensions (like completeness) have an overall lower leakage degree compared with subjective ones (like fairness). This suggests that preference leakage tends to be more significant in objective questions and dimensions, where the contaminated model is more likely to receive biased preference.

## **6 Conclusion**

In this work, we formally highlight the preference leakage problem in LLM-as-a-judge systems. The results of our main experiment, measured using the proposed preference leakage score, reveal a clear bias in each judge toward their respective student model. We also observe that this bias is more pronounced in certain question types and smaller student models. Furthermore, we conduct additional analysis on various factors, including the relationship between the data generator and judge LLMs, model tuning techniques, data mixing strategies, and real-world applications. Our findings suggest that preference leakage can cause significant bias across diverse scenarios. Finally, through recognition and category analyses, we investigate the underlying mechanisms of preference leakage, demonstrating that it is a challenging and hard-to-detect issue, especially in subjective questions and judgment dimensions. In the future, we aim to explore methods for detecting, preventing, and


------------------------- PAGINA 10 --------------------------

mitigating this evolving challenge in LLM-as-a-judge systems. We leave the exploration of detection, mitigation and calibration methods of preference leakage for future works.

## **References**

- [1] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. _ArXiv preprint_ , abs/2303.08774, 2023. URL https://arxiv.org/abs/ 2303.08774.

- [2] Simone Balloccu, Patrícia Schmidtová, Mateusz Lango, and Ondˇrej Dušek. Leak, cheat, repeat: Data contamination and evaluation malpractices in closed-source llms. In _Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 67–93, 2024.

- [3] Sebastian Bordt, Harsha Nori, and Rich Caruana. Elephants never forget: Testing language models for memorization of tabular data. In _NeurIPS 2023 Second Table Representation Learning Workshop_ , 2024.

- [4] Guiming Hardy Chen, Shunian Chen, Ziche Liu, Feng Jiang, and Benyou Wang. Humans or llms as the judge? a study on judgement biases. _arXiv preprint arXiv:2402.10669_ , 2024.

- [5] Wei-Lin Chen, Zhepei Wei, Xinyu Zhu, Shi Feng, and Yu Meng. Do llm evaluators prefer themselves for a reason? _arXiv preprint arXiv:2504.03846_ , 2025.

- [6] Ganqu Cui, Lifan Yuan, Ning Ding, Guanming Yao, Bingxiang He, Wei Zhu, Yuan Ni, Guotong Xie, Ruobing Xie, Yankai Lin, et al. Ultrafeedback: Boosting language models with scaled ai feedback. In _Forty-first International Conference on Machine Learning_ , 2024.

- [7] Chunyuan Deng, Yilun Zhao, Yuzhao Heng, Yitong Li, Jiannan Cao, Xiangru Tang, and Arman Cohan. Unveiling the spectrum of data contamination in language models: A survey from detection to remediation. _arXiv preprint arXiv:2406.14644_ , 2024.

- [8] Chunyuan Deng, Yilun Zhao, Xiangru Tang, Mark Gerstein, and Arman Cohan. Investigating data contamination in modern benchmarks for large language models. In _Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)_ , pages 8698–8711, 2024.

- [9] Jesse Dodge, Maarten Sap, Ana Marasovi´c, William Agnew, Gabriel Ilharco, Dirk Groeneveld, Margaret Mitchell, and Matt Gardner. Documenting large webtext corpora: A case study on the colossal clean crawled corpus. In _Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing_ , pages 1286–1305, 2021.

- [10] Qingxiu Dong, Lei Li, Damai Dai, Ce Zheng, Jingyuan Ma, Rui Li, Heming Xia, Jingjing Xu, Zhiyong Wu, Baobao Chang, et al. A survey on in-context learning. In _Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing_ , pages 1107–1128, 2024.

- [11] Yihong Dong, Xue Jiang, Huanyu Liu, Zhi Jin, Bin Gu, Mengfei Yang, and Ge Li. Generalization or memorization: Data contamination and trustworthy evaluation for large language models. _arXiv preprint arXiv:2402.15938_ , 2024.

- [12] Sunny Duan, Mikail Khona, Abhiram Iyer, Rylan Schaeffer, and Ila R Fiete. Uncovering latent memories: Assessing data leakage and memorization patterns in large language models. _arXiv preprint arXiv:2406.14549_ , 2024.

- [13] Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. _arXiv preprint arXiv:2407.21783_ , 2024.

- [14] Yann Dubois, Balázs Galambosi, Percy Liang, and Tatsunori B Hashimoto. Length-controlled alpacaeval: A simple way to debias automatic evaluators. _arXiv preprint arXiv:2404.04475_ , 2024.


------------------------- PAGINA 11 --------------------------

- [15] Ruyi Gan, Ziwei Wu, Renliang Sun, Junyu Lu, Xiaojun Wu, Dixiang Zhang, Kunhao Pan, Ping Yang, Qi Yang, Jiaxing Zhang, et al. Ziya2: Data-centric learning is all llms need. _arXiv preprint arXiv:2311.03301_ , 2023.

- [16] Mingqi Gao, Jie Ruan, Renliang Sun, Xunjian Yin, Shiping Yang, and Xiaojun Wan. Human-like summarization evaluation with chatgpt. _arXiv preprint arXiv:2304.02554_ , 2023.

- [17] Shahriar Golchin and Mihai Surdeanu. Time travel in llms: Tracing data contamination in large language models. _arXiv preprint arXiv:2308.08493_ , 2023.

- [18] Jamie Hayes, Ilia Shumailov, William P Porter, and Aneesh Pappu. Measuring memorization in rlhf for code completion. In _The Thirteenth International Conference on Learning Representations_ .

- [19] Shengding Hu, Yifan Luo, Huadong Wang, Xingyi Cheng, Zhiyuan Liu, and Maosong Sun. Won’t get fooled again: Answering questions with false premises. In _Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 5626–5643, 2023.

- [20] Yue Huang, Jiawen Shi, Yuan Li, Chenrui Fan, Siyuan Wu, Qihui Zhang, Yixin Liu, Pan Zhou, Yao Wan, Neil Zhenqiang Gong, et al. Metatool benchmark for large language models: Deciding whether to use tools and which to use. _arXiv preprint arXiv:2310.03128_ , 2023.

- [21] Yue Huang, Lichao Sun, Haoran Wang, Siyuan Wu, Qihui Zhang, Yuan Li, Chujie Gao, Yixin Huang, Wenhan Lyu, Yixuan Zhang, et al. Position: Trustllm: Trustworthiness in large language models. In _International Conference on Machine Learning_ , pages 20166–20270. PMLR, 2024.

- [22] Aaron Jaech, Adam Kalai, Adam Lerer, Adam Richardson, Ahmed El-Kishky, Aiden Low, Alec Helyar, Aleksander Madry, Alex Beutel, Alex Carney, et al. Openai o1 system card. _arXiv preprint arXiv:2412.16720_ , 2024.

- [23] Albert Q Jiang, Alexandre Sablayrolles, Arthur Mensch, Chris Bamford, Devendra Singh Chaplot, Diego de las Casas, Florian Bressand, Gianna Lengyel, Guillaume Lample, Lucile Saulnier, et al. Mistral 7b. _arXiv preprint arXiv:2310.06825_ , 2023.

- [24] Bohan Jiang, Dawei Li, Zhen Tan, Xinyi Zhou, Ashwin Rao, Kristina Lerman, H Russell Bernard, and Huan Liu. Assessing the impact of conspiracy theories using large language models. _arXiv preprint arXiv:2412.07019_ , 2024.

- [25] Minhao Jiang, Ken Ziyu Liu, Ming Zhong, Rylan Schaeffer, Siru Ouyang, Jiawei Han, and Sanmi Koyejo. Investigating data contamination for pre-training language models. _arXiv preprint arXiv:2401.06059_ , 2024.

- [26] Seungone Kim, Jamin Shin, Yejin Cho, Joel Jang, Shayne Longpre, Hwaran Lee, Sangdoo Yun, Seongjin Shin, Sungdong Kim, James Thorne, et al. Prometheus: Inducing fine-grained evaluation capability in language models. In _The Twelfth International Conference on Learning Representations_ , 2023.

- [27] Seungone Kim, Juyoung Suk, Shayne Longpre, Bill Yuchen Lin, Jamin Shin, Sean Welleck, Graham Neubig, Moontae Lee, Kyungjae Lee, and Minjoon Seo. Prometheus 2: An open source language model specialized in evaluating other language models. _arXiv preprint arXiv:2405.01535_ , 2024.

- [28] Ryan Koo, Minhwa Lee, Vipul Raheja, Jong Inn Park, Zae Myung Kim, and Dongyeop Kang. Benchmarking cognitive biases in large language models as evaluators. _arXiv preprint arXiv:2309.17012_ , 2023.

- [29] Ryan Koo, Minhwa Lee, Vipul Raheja, Jong Inn Park, Zae Myung Kim, and Dongyeop Kang. Benchmarking cognitive biases in large language models as evaluators. In _ACL (Findings)_ , 2024.

- [30] Andreas Köpf, Yannic Kilcher, Dimitri von Rütte, Sotiris Anagnostidis, Zhi Rui Tam, Keith Stevens, Abdullah Barhoum, Duc Nguyen, Oliver Stanley, Richárd Nagyfi, et al. Openassistant conversations-democratizing large language model alignment. _Advances in Neural Information Processing Systems_ , 36, 2024.


------------------------- PAGINA 12 --------------------------

- [31] Harrison Lee, Samrat Phatale, Hassan Mansoor, Thomas Mesnard, Johan Ferret, Kellie Ren Lu, Colton Bishop, Ethan Hall, Victor Carbune, Abhinav Rastogi, et al. Rlaif vs. rlhf: Scaling reinforcement learning from human feedback with ai feedback. In _Forty-first International Conference on Machine Learning_ , 2024.

- [32] Sunbowen Lee, Junting Zhou, Chang Ao, Kaige Li, Xinrun Du, Sirui He, Jiaheng Liu, Min Yang, Zhoufutu Wen, and Shiwen Ni. Distillation quantification for large language models. _arXiv preprint arXiv:2501.12619_ , 2025.

- [33] Changmao Li and Jeffrey Flanigan. Task contamination: Language models may not be few-shot anymore. In _Proceedings of the AAAI Conference on Artificial Intelligence_ , volume 38, pages 18471–18480, 2024.

- [34] Dawei Li, Bohan Jiang, Liangjie Huang, Alimohammad Beigi, Chengshuai Zhao, Zhen Tan, Amrita Bhattacharjee, Yuxuan Jiang, Canyu Chen, Tianhao Wu, et al. From generation to judgment: Opportunities and challenges of llm-as-a-judge. _arXiv preprint arXiv:2411.16594_ , 2024.

- [35] Dawei Li, Zhen Tan, Tianlong Chen, and Huan Liu. Contextualization distillation from large language model for knowledge graph completion. _arXiv preprint arXiv:2402.01729_ , 2024.

- [36] Dawei Li, Shu Yang, Zhen Tan, Jae Young Baik, Sunkwon Yun, Joseph Lee, Aaron Chacko, Bojian Hou, Duy Duong-Tran, Ying Ding, et al. Dalk: Dynamic co-augmentation of llms and kg to answer alzheimer’s disease questions with scientific literature. _arXiv preprint arXiv:2405.04819_ , 2024.

- [37] Dawei Li, Zhen Tan, and Huan Liu. Exploring large language models for feature selection: A data-centric perspective. _ACM SIGKDD Explorations Newsletter_ , 26(2):44–53, 2025.

- [38] Ming Li, Lichang Chen, Jiuhai Chen, Shwai He, Jiuxiang Gu, and Tianyi Zhou. Selective reflection-tuning: Student-selected data recycling for llm instruction-tuning. _arXiv preprint arXiv:2402.10110_ , 2024.

- [39] Tianle Li, Wei-Lin Chiang, Evan Frick, Lisa Dunlap, Tianhao Wu, Banghua Zhu, Joseph E Gonzalez, and Ion Stoica. From crowdsourced data to high-quality benchmarks: Arena-hard and benchbuilder pipeline. _arXiv preprint arXiv:2406.11939_ , 2024.

- [40] Xuechen Li, Tianyi Zhang, Yann Dubois, Rohan Taori, Ishaan Gulrajani, Carlos Guestrin, Percy Liang, and Tatsunori B Hashimoto. Alpacaeval: An automatic evaluator of instruction-following models, 2023.

- [41] Chin-Yew Lin. Rouge: A package for automatic evaluation of summaries. In _Text summarization branches out_ , pages 74–81, 2004.

- [42] Stephanie Lin, Jacob Hilton, and Owain Evans. Truthfulqa: Measuring how models mimic human falsehoods. In _Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 3214–3252, 2022.

- [43] Chia-Wei Liu, Ryan Lowe, Iulian Serban, Mike Noseworthy, Laurent Charlin, and Joelle Pineau. How NOT to evaluate your dialogue system: An empirical study of unsupervised evaluation metrics for dialogue response generation. In Jian Su, Kevin Duh, and Xavier Carreras, editors, _Proceedings of the 2016 Conference on Empirical Methods in Natural Language Processing_ , pages 2122–2132, Austin, Texas, 2016. Association for Computational Linguistics. doi: 10.18653/v1/D16-1230. URL https://aclanthology.org/D16-1230.

- [44] Wei Liu, Weihao Zeng, Keqing He, Yong Jiang, and Junxian He. What makes good data for alignment? a comprehensive study of automatic data selection in instruction tuning. In _The Twelfth International Conference on Learning Representations_ , 2024.

- [45] Xiao Liu, Xuanyu Lei, Shengyuan Wang, Yue Huang, Zhuoer Feng, Bosi Wen, Jiale Cheng, Pei Ke, Yifan Xu, Weng Lam Tam, et al. Alignbench: Benchmarking chinese alignment of large language models. _arXiv preprint arXiv:2311.18743_ , 2023.


------------------------- PAGINA 13 --------------------------

- [46] Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, et al. Agentbench: Evaluating llms as agents. _arXiv preprint arXiv:2308.03688_ , 2023.

- [47] Yiqi Liu, Nafise Sadat Moosavi, and Chenghua Lin. Llms as narcissistic evaluators: When ego inflates evaluation scores. In _Findings of the Association for Computational Linguistics ACL 2024_ , pages 12688–12701, 2024.

- [48] Jinjie Ni, Fuzhao Xue, Xiang Yue, Yuntian Deng, Mahir Shah, Kabir Jain, Graham Neubig, and Yang You. Mixeval: Deriving wisdom of the crowd from llm benchmark mixtures. _arXiv preprint arXiv:2406.06565_ , 2024.

- [49] Arjun Panickssery, Samuel R Bowman, and Shi Feng. Llm evaluators recognize and favor their own generations. _arXiv preprint arXiv:2404.13076_ , 2024.

- [50] Kishore Papineni, Salim Roukos, Todd Ward, and Wei-Jing Zhu. Bleu: a method for automatic evaluation of machine translation. In _Proceedings of the 40th annual meeting of the Association for Computational Linguistics_ , pages 311–318, 2002.

- [51] Rafael Rafailov, Archit Sharma, Eric Mitchell, Christopher D Manning, Stefano Ermon, and Chelsea Finn. Direct preference optimization: Your language model is secretly a reward model. _Advances in Neural Information Processing Systems_ , 36, 2024.

- [52] Javier Rando, Jie Zhang, Nicholas Carlini, and Florian Tramèr. Adversarial ml problems are getting harder to solve and to evaluate. _arXiv preprint arXiv:2502.02260_ , 2025.

- [53] Ehud Reiter. A structured review of the validity of BLEU. _Computational Linguistics_ , 44 (3):393–401, 2018. doi: 10.1162/coli_a_00322. URL https://aclanthology.org/ J18-3002.

- [54] Jiawen Shi, Zenghui Yuan, Yinuo Liu, Yue Huang, Pan Zhou, Lichao Sun, and Neil Zhenqiang Gong. Optimization-based prompt injection attack to llm-as-a-judge. In _Proceedings of the 2024 on ACM SIGSAC Conference on Computer and Communications Security_ , CCS ’24, page 660–674, New York, NY, USA, 2024. Association for Computing Machinery. ISBN 9798400706363. doi: 10.1145/3658644.3690291. URL https://doi.org/10.1145/ 3658644.3690291.

- [55] Renliang Sun, Mengyuan Liu, Shiping Yang, Rui Wang, Junqing He, and Jiaxing Zhang. Fostering natural conversation in large language models with nico: a natural interactive conversation dataset. _arXiv preprint arXiv:2408.09330_ , 2024.

- [56] Tianxiang Sun, Xiaotian Zhang, Zhengfu He, Peng Li, Qinyuan Cheng, Xiangyang Liu, Hang Yan, Yunfan Shao, Qiong Tang, Shiduo Zhang, Xingjian Zhao, Ke Chen, Yining Zheng, Zhejian Zhou, Ruixiao Li, Jun Zhan, Yunhua Zhou, Linyang Li, Xiaogui Yang, Lingling Wu, Zhangyue Yin, Xuanjing Huang, Yu-Gang Jiang, and Xipeng Qiu. Moss: An open conversational large language model. _Machine Intelligence Research_ , 2024. ISSN 2731-5398. URL https://github.com/OpenMOSS/MOSS.

- [57] Zhen Tan, Dawei Li, Song Wang, Alimohammad Beigi, Bohan Jiang, Amrita Bhattacharjee, Mansooreh Karami, Jundong Li, Lu Cheng, and Huan Liu. Large language models for data annotation and synthesis: A survey. In _Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing_ , pages 930–957, 2024.

- [58] Gemini Team, Petko Georgiev, Ving Ian Lei, Ryan Burnell, Libin Bai, Anmol Gulati, Garrett Tanzer, Damien Vincent, Zhufeng Pan, Shibo Wang, et al. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. _arXiv preprint arXiv:2403.05530_ , 2024.

- [59] Aman Singh Thakur, Kartik Choudhary, Venkat Srinik Ramayapally, Sankaran Vaidyanathan, and Dieuwke Hupkes. Judging the judges: Evaluating alignment and vulnerabilities in llms-asjudges. _arXiv preprint arXiv:2406.12624_ , 2024.

- [60] Yongqi Tong, Dawei Li, Sizhe Wang, Yujia Wang, Fei Teng, and Jingbo Shang. Can llms learn from previous mistakes? investigating llms’ errors to boost for reasoning. _arXiv preprint arXiv:2403.20046_ , 2024.


------------------------- PAGINA 14 --------------------------

- [61] Somin Wadhwa, Chantal Shaib, Silvio Amir, and Byron C Wallace. Who taught you that? tracing teachers in model distillation. _arXiv preprint arXiv:2502.06659_ , 2025.

- [62] Sizhe Wang, Yongqi Tong, Hengyuan Zhang, Dawei Li, Xin Zhang, and Tianlong Chen. Bpo: Towards balanced preference optimization between knowledge breadth and depth in alignment. _arXiv preprint arXiv:2411.10914_ , 2024.

- [63] Koki Wataoka, Tsubasa Takahashi, and Ryokan Ri. Self-preference bias in llm-as-a-judge. _arXiv preprint arXiv:2410.21819_ , 2024.

- [64] Colin White, Samuel Dooley, Manley Roberts, Arka Pal, Ben Feuer, Siddhartha Jain, Ravid Shwartz-Ziv, Neel Jain, Khalid Saifullah, Siddartha Naidu, et al. Livebench: A challenging, contamination-free llm benchmark. _arXiv preprint arXiv:2406.19314_ , 2024.

- [65] Siyuan Wu, Yue Huang, Chujie Gao, Dongping Chen, Qihui Zhang, Yao Wan, Tianyi Zhou, Xiangliang Zhang, Jianfeng Gao, Chaowei Xiao, et al. Unigen: A unified framework for textual dataset generation using large language models. _arXiv preprint arXiv:2406.18966_ , 2024.

- [66] Can Xu, Qingfeng Sun, Kai Zheng, Xiubo Geng, Pu Zhao, Jiazhan Feng, Chongyang Tao, and Daxin Jiang. Wizardlm: Empowering large language models to follow complex instructions. _arXiv preprint arXiv:2304.12244_ , 2023.

- [67] Cheng Xu, Shuhao Guan, Derek Greene, M Kechadi, et al. Benchmark data contamination of large language models: A survey. _arXiv preprint arXiv:2406.04244_ , 2024.

- [68] Wenda Xu, Guanglei Zhu, Xuandong Zhao, Liangming Pan, Lei Li, and William Wang. Pride and prejudice: Llm amplifies self-bias in self-refinement. In _Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 15474–15492, 2024.

- [69] An Yang, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng, Bowen Yu, Chengyuan Li, Dayiheng Liu, Fei Huang, Haoran Wei, et al. Qwen2. 5 technical report. _arXiv preprint arXiv:2412.15115_ , 2024.

- [70] Shiping Yang, Renliang Sun, and Xiaojun Wan. A new dataset and empirical study for sentence simplification in chinese. In _Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 8306–8321, 2023.

- [71] Feng Yao, Yufan Zhuang, Zihao Sun, Sunan Xu, Animesh Kumar, and Jingbo Shang. Data contamination can cross language barriers. _arXiv preprint arXiv:2406.13236_ , 2024.

- [72] Jiayi Ye, Yanbo Wang, Yue Huang, Dongping Chen, Qihui Zhang, Nuno Moniz, Tian Gao, Werner Geyer, Chao Huang, Pin-Yu Chen, et al. Justice or prejudice? quantifying biases in llm-as-a-judge. _arXiv preprint arXiv:2410.02736_ , 2024.

- [73] Hengyuan Zhang, Dawei Li, Yanran Li, Chenming Shang, Chufan Shi, and Yong Jiang. Assisting language learners: Automated trans-lingual definition generation via contrastive prompt learning. _arXiv preprint arXiv:2306.06058_ , 2023.

- [74] Hengyuan Zhang, Chenming Shang, Sizhe Wang, Dongdong Zhang, Feng Yao, Renliang Sun, Yiyao Yu, Yujiu Yang, and Furu Wei. Shifcon: Enhancing non-dominant language capabilities with a shift-based contrastive framework. _arXiv preprint arXiv:2410.19453_ , 2024.

- [75] Hengyuan Zhang, Yanru Wu, Dawei Li, Zacc Yang, Rui Zhao, Yong Jiang, and Fei Tan. Balancing speciality and versatility: a coarse to fine framework for supervised fine-tuning large language model. _arXiv preprint arXiv:2404.10306_ , 2024.

- [76] Qihui Zhang, Chujie Gao, Dongping Chen, Yue Huang, Yixin Huang, Zhenyang Sun, Shilin Zhang, Weiye Li, Zhengyan Fu, Yao Wan, and Lichao Sun. LLM-as-a-coauthor: Can mixed human-written and machine-generated text be detected? In Kevin Duh, Helena Gomez, and Steven Bethard, editors, _Findings of the Association for Computational Linguistics: NAACL 2024_ , pages 409–436, Mexico City, Mexico, June 2024. Association for Computational Linguistics. doi: 10.18653/v1/2024.findings-naacl.29. URL https: //aclanthology.org/2024.findings-naacl.29/.


------------------------- PAGINA 15 --------------------------

- [77] Tianyi Zhang, Varsha Kishore, Felix Wu, Kilian Q Weinberger, and Yoav Artzi. Bertscore: Evaluating text generation with bert. In _International Conference on Learning Representations_ , 2020.

- [78] Xiaoying Zhang, Baolin Peng, Ye Tian, Jingyan Zhou, Lifeng Jin, Linfeng Song, Haitao Mi, and Helen Meng. Self-alignment for factuality: Mitigating hallucinations in LLMs via self-evaluation. In Lun-Wei Ku, Andre Martins, and Vivek Srikumar, editors, _Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)_ , pages 1946–1965, Bangkok, Thailand, August 2024. Association for Computational Linguistics. doi: 10.18653/v1/2024.acl-long.107. URL https://aclanthology.org/ 2024.acl-long.107/.

- [79] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, et al. Judging llm-as-a-judge with mt-bench and chatbot arena. _Advances in Neural Information Processing Systems_ , 36:46595–46623, 2023.

- [80] Yaowei Zheng, Richong Zhang, Junhao Zhang, Yanhan Ye, Zheyan Luo, Zhangchi Feng, and Yongqiang Ma. Llamafactory: Unified efficient fine-tuning of 100+ language models. _arXiv preprint arXiv:2403.13372_ , 2024.

- [81] Ming Zhong, Yang Liu, Da Yin, Yuning Mao, Yizhu Jiao, Pengfei Liu, Chenguang Zhu, Heng Ji, and Jiawei Han. Towards a unified multi-dimensional evaluator for text generation. In Yoav Goldberg, Zornitsa Kozareva, and Yue Zhang, editors, _Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing, EMNLP 2022, Abu Dhabi, United Arab Emirates, December 7-11, 2022_ , pages 2023–2038. Association for Computational Linguistics, 2022. doi: 10.18653/V1/2022.EMNLP-MAIN.131. URL https://doi.org/10.18653/ v1/2022.emnlp-main.131.

- [82] Ming Zhong, Aston Zhang, Xuewei Wang, Rui Hou, Wenhan Xiong, Chenguang Zhu, Zhengxing Chen, Liang Tan, Chloe Bi, Mike Lewis, et al. Law of the weakest link: Cross capabilities of large language models. _arXiv preprint arXiv:2409.19951_ , 2024.

- [83] Chunting Zhou, Pengfei Liu, Puxin Xu, Srinivasan Iyer, Jiao Sun, Yuning Mao, Xuezhe Ma, Avia Efrat, Ping Yu, Lili Yu, et al. Lima: Less is more for alignment. _Advances in Neural Information Processing Systems_ , 36, 2024.

- [84] Mingchen Zhuge, Changsheng Zhao, Dylan Ashley, Wenyi Wang, Dmitrii Khizbullin, Yunyang Xiong, Zechun Liu, Ernie Chang, Raghuraman Krishnamoorthi, Yuandong Tian, et al. Agentas-a-judge: Evaluate agents with agents. _arXiv preprint arXiv:2410.10934_ , 2024.


------------------------- PAGINA 16 --------------------------

## **A Preliminary Study of Preference Leakage in Real World**

In our preliminary study, we investigate whether preference leakage is a real-world issue in mainstream leaderboards and benchmarks. To this end, we examine two widely used LLM-as-a-judge leaderboards (AlpacaEval 2.0 and Arena-Hard) and a well-known benchmark (MTBench). All three rely on GPT-4 as the judge model and report pairwise judgment results for various LLMs. Our analysis reveals that several candidate models distilled from GPT-4 or other GPT-series models (e.g., Vicuna and Alpaca) appear across all these leaderboards and benchmarks, suggesting that preference leakage is a pervasive issue in these datasets. Besides, we also examine if preference leakage exists in LLM-relevant research studies and also find a bunch of work utilizing the same or related model(s) to do distillation/ data synthesis and evaluation [70, 44, 31, 38, 62, 55]. All of these suggest preference leakage to be a widespread problem in both LLM-as-a-judge datasets and LLM-relevant research.

## **B Experiment Details**

### **B.1 Training Details**

We use LLaMA-Factory [80], an efficient LLM tuning library for our experiment. The maximum sequence length is set to 1024 tokens, and a cutoff length of 1024 tokens is enforced to prevent excessive tokenization. The data preprocessing will be done in parallel with 16 workers to speed up the preparation process. The training use a per-device batch size of 2, with gradient accumulation over 2 steps to simulate a larger batch size for SFT and a per-device batch size of 1, with gradient accumulation over 4 steps to simulate a larger batch size for DPO. The learning rate is set to 1.0e-5 and each model will be trained for 3 epochs. A cosine learning rate scheduler is used with a warmup ratio of 0.1 to gradually increase the learning rate during the initial steps. All of the experiments use BF16 precision to speed up training while maintaining numerical stability. All the experiments are conducted in an 8 Nvidia A100 GPU cluster with CUDA version 11.8.

Table 6: A case on AlpacaEval 2.0 with the model pair Mistral-GPT-4o vs Mistral-Gemini-1.5 to demonstrate how the preference leakage score is calculated.

|Judge Model|Mistral-GPT-4o vs Mistral-Gemini-1.5|
|---|---|
||Mistral-GPT-4o Wins<br>Mistral-Gemini-1.5 Wins|
|GPT-4o|55.1%<br>44.9%|
|Gemini-1.5|36.8%<br>63.2%|
|Preference Leakage Score|18.4%|

### **B.2 Detailed Explanation for Preference Leakage Score**

We present a case in Table 6 to show how we calculate the preference leakage score for the MistralGPT-4o vs Mistral-Gemini-1.5 pair on AlpacaEval 2.0. Based on the definition of preference leakage score, we first calculate:

After that, we calculate the preference leakage score:

PLS(Mistral-GPT-4o _,_ Mistral-Gemini-1.5) = <u>� 55</u> _<u>.</u>_ <u>451</u> _−._ <u>4595</u> _<u>.</u>_ <u>95 �</u> + <u>� 63</u> _<u>.</u>_ <u>542</u> _−._ <u>5405</u> _<u>.</u>_ <u>05 �</u> = 18 _._ 4% (9) 2

### **B.3 Manual Annotation Details & Results**

While we have concluded that student model pairs with similar performance or more powerful student models tend to exhibit greater preference leakage, we also examine whether different data generator


------------------------- PAGINA 17 --------------------------

and judge LLMs contribute to varying degrees of preference leakage. We randomly sample 100 questions from AlpacaEval 2.0 and ask three well-trained annotators to conduct pairwise comparisons of the responses from each model pair for these questions. For annotation efficiency, we also develop an annotation tool that involves the function of uploading multiple model responses, jumping to specific problems, and downloading annotation results (Figure 7). After annotation, we adopt the majority voting to get the final label for each response pair. We also calculate the average agreement of three annotators and find it to be 78.6, indicating a relatively consistent annotation result.

Analyzing the manual annotation results presented in Figure 6, we observe that Gemini-1.5 shows a strong bias toward its students, followed by GPT-4o, with LLaMA-3.3 displaying the least bias. This variation in preference leakage may stem from differences in the level of leaked preference in the synthetic responses generated by the data generator LLMs. For instance, an LLM with a distinctive style or format in its responses offers more opportunities for student models to learn these characteristics, potentially leading to more pronounced preference leakage during evaluation. Future work could further quantify the extent of leaked preference for each data generator model.

<!-- Start of picture text -->
Mistral-GPT4o vs Mistral-Gemini-1.5 Mistral-GPT4o vs Mistral-LLaMA-3.3 Mistral-LLaMA-3.3 vs Mistral-Gemini-1.5<br>GPT-4o 58.4% 41.6% 67.8% 32.2% 46.0% 54.0%<br>LLaMA-3.3 49.4% 50.6% 72.1% 27.9% 39.0% 61.0%<br>Gemini-1.5 40.2% 59.8% 76.2% 23.8% 17.1% 82.9%<br>Human 53.0% 47.0% 62.0% 38.0% 36.0% 64.0%<br>0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0% 0.0% 20.0% 40.0% 60.0% 80.0% 100.0%<br>Model A Wins Model B Wins<br>Judge Model<br><!-- End of picture text -->

Figure 6: Manual annotation result on 100 randomly selected samples from AlpacaEval 2.0.

## **C Learning Method Analysis Details**

The table below presents the prompt we use to generate synthetic pairwise feedback from each model.

### Pairwise Feedback Prompt

Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. Your evaluation should consider correctness and helpfulness. You will be given assistant A’s answer, and assistant B’s answer. Your job is to evaluate which assistant’s answer is better. You should independently solve the user question step-by-step first. Then compare both assistants’ answers with your answer. Identify and correct any mistakes. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. After providing your explanation, output your final verdict by strictly following this format: "[[A]]" if assistant A is better, "[[B]]" if assistant B is better. ## Instruction: [The Start of Assistant A’s Answer] [RESPONSE A] [The End of Assistant A’s Answer] [The Start of Assistant B’s Answer] [RESPONSE B] [The End of Assistant B’s Answer]


------------------------- PAGINA 18 --------------------------

Please output the generated content in a json format, for example: { "reason": // string, reasons behind the chosen preferred answer "prefered answer": // string, the prefered answer you selected, [[A]] or [[B]] } Formatted the abovementioned schema and produce the reason and preferred answer:

## **D Real-world Impact Analysis Details**

In the real-world impact analysis section, we use the models that appear in both Chatbot Arena and AlpacaEval 2.0 leaderboard, including: GPT-4o-2024-05-13, GPT-4o-mini-2024-07-18, MetaLlama-3.1-405B-Instruct-bf16, GPT-4-Turbo-2024-04-09, GPT-4-1106-preview, Meta-Llama-3.170B-Instruct, Claude 3 Opus, Llama-3-70B-Instruct, Claude 3 Sonnet, Qwen2-72B-Instruct, GPT-40314, Meta-Llama-3.1-8B-Instruct, GPT-4-0613, Mistral-Large-2402, Llama-3-8B-Instruct, Command R (04-2024), Mistral Medium, Mixtral-8x22b-Instruct-v0.1, Qwen1.5-72B-Chat, Gemini Pro, Yi-34B-Chat, Mixtral-8x7B-Instruct-v0.1, Qwen1.5-14B-Chat, GPT-3.5-Turbo-0125, DBRX-InstructPreview, Tulu-2-DPO-70B, Llama-2-70B-chat, Vicuna-33B, Gemma-1.1-7B-it, OpenHermes-2.5Mistral-7B, Mistral-7B-Instruct-v0.2, Qwen1.5-7B-Chat, GPT-3.5-Turbo-1106, Llama-2-13b-chat, WizardLM-13b-v1.2, Vicuna-13B, Llama-2-7B-chat, Guanaco-33B, Vicuna-7B, Gemma-2B-it, OpenAssistant-Pythia-12B.

## **E Recogniton Analysis Details**

The table below presents the pointwise and pairwise prompts we use for the recognition analysis.

### Pointwise Recognition Prompt

Given an instruction and a response, your task is to judge whether this response is generated by a model that is trained on a synthetic dataset you produced (your student model). ## Instruction: [INSTRUCTION] ## Response: [Response]

Please output the generated content in a json format, for example: "reason": // string, reasons behind the judgment "judgment": // string, whether the answer is generated by your student model, choose from yes or no Formatted the abovementioned schema and produce the reason and judgment:

### Pairwise Recognition Prompt

Given an instruction and two responses, your task is to judge which response is generated by a model that is trained on a synthetic dataset you produced (your student model).

## Instruction: [INSTRUCTION] ## Response1: [Response 1] ## Response2: [Response 2]


------------------------- PAGINA 19 --------------------------

Please output the generated content in a json format, for example: "reason": // string, reasons behind the judgment "judgment": // int, 1 or 2, means response1 or response2 is from your student model Formatted the abovementioned schema and produce the reason and judgment:

For response classification, we split all the response from three student models into training (80%) and testing (20%) subsets. Then, we finetune a BERT-base-uncased model in the training set. The model is trained for 3 epochs with a learning rate of 2e-5, a batch size of 16 for both training and evaluation, and a weight decay of 0.01, with evaluations conducted at the end of each epoch.

## **F Category Analysis Details**

The tables below present the prompt we use for question type and judgment dimension cateogory analysis.

### Question Type Categorization Prompt

Given a question, please categorize it to one of the following categories:

1. Computer Science & Programming 2. Mathematics & Statistics

3. Science & Engineering 4. Business & Finance

5. Writing & Communication

6. Social & Daily Life 7. Others

## Question: [QUESTION]

Please output the generated content in a json format, for example: { "question category": // string, specific category name, such as "Computer Science & Programming" } Formatted the abovementioned schema and categorize the given question:

### Judgment Dimension Categorization Prompt

Given a pairwise comparison judgment made by an AI, please categorize each considered aspect in the rationale to one of the following categories:

{ "Factuality": "Whether the information provided in the response is accurate, based on reliable facts and data.", "User Satisfaction": "Whether the response meets the user’s question and needs, and provides a comprehensive and appropriate answer to the question.", "Logical Coherence": "Whether the response maintains overall consistency and logical coherence between different sections, avoiding self-contradiction.",


------------------------- PAGINA 20 --------------------------

"Richness": "Whether the response includes rich info, depth, context, diversity, detailed explanations and examples to meet user needs and provide a comprehensive understanding.", "Creativity": "Whether the response is innovative or unique, providing novel insights or solutions.", "Fairness and Responsibility": "Whether the advice or information provided in the response is feasible, carries acertain degree of responsibility, and considers potential risks and consequences.", "Completeness": "Whether the response provides sufficient information and details to meet the user’s needs, and whether it avoids omitting important aspects.", "Clarity": "Whether the response is clear and understandable, and whether it uses concise language and structure so that the user can easily understand it.", "Others": "Other aspects which is not listed above." } ## Judgment: [JUDGMENT] Please output the generated content in a json format, for example: { "Factuality": // list, all aspects that belong to this category, such as ["correctness", "mistakes"] ... } Formatted the abovementioned schema and categorize aspects in the judgment:

Figure 7: The annotation tool we develop for annotation efficiency.

## **G Broader Impact**

By revealing preference leakage, this work could help build more trustworthy and ethically grounded AI systems. The relatedness between data generators and evaluators can systematically bias evaluations, potentially compromising the fairness and reliability of the automatic evaluation paradigm. These biased evaluations may indirectly affect downstream tasks such as AI alignment and decisionmaking systems, leading to unintended ethical risks. To mitigate preference leakage, we hope that researchers will propose more reliable evaluation methods, diversify training data sources, and develop contamination-resistant benchmarks in the future.
