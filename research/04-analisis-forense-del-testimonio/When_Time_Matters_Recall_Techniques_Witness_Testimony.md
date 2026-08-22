# When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality

> **En [`docs/pvb.md`](../../docs/pvb.md): `[12]`** · **En [`docs/critica.md`](../../docs/critica.md): no lo cita**  
> Solà-Sales, S., Alzetta, C., Moret-Tatay, C., & Dell’Orletta, F. (2025). *When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality*. Information, 16(2).  
> 
> Secciones de `pvb.md`: 4. ARENA COMPETITIVA  
> Fuente convertida: `1-papersMD/2-Pilar2-Cómo/When_Time_Matters_Recall_Techniques_Witness_Testimony.md`


**Archivo origen:** `1-papers/2-Pilar2-Cómo/When Time Matters.pdf`  
**Páginas:** 24  
**Nota:** los separadores `PAGINA n` corresponden a la página física del PDF. Los encabezados y pies de página repetidos se conservan solo en su primera aparición.


------------------------- PAGINA 1 --------------------------

_Article_

**When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality Sara Solà-Sales**<sup>**1,**</sup> *****<sup>**,†**</sup> **, Chiara Alzetta**<sup>**2,†**</sup> **, Carmen Moret-Tatay**<sup>**3**</sup> **and Felice Dell’Orletta**<sup>**2**</sup>

- 1 Doctoral School, Catholic University of Valencia San Vicente Mártir, 46002 Valencia, Spain

- 2 ItaliaNLPLab, Institute for Computational Linguistics “A. Zampolli” (CNR-ILC), Via G. Moruzzi 1, 56124 Pisa, Italy; chiara.alzetta@ilc.cnr.it (C.A.); felice.dellorletta@ilc.cnr.it (F.D.)

- 3 MEB Lab, Faculty of Psychology, Universidad Católica de Valencia San Vicente Mártir, 46100 Valencia, Spain; mariacarmen.moret@ucv.es

- Correspondence: sara.sola@mail.ucv.es

- These authors contributed equally to this work.

**Abstract:** Mental reconstruction (MRC) and Free Recall (FR) have been recognized for enhancing the quality of witness statements. However, the mechanisms underlying this association remain insufficiently understood. This study explores how the time allocated to MRC and FR and variations in educational level influence the quality of eyewitness testimonies. Testimony quality is evaluated based on manually annotated content information provided by experts in testimony assessment, which measures adherence to the events. This is further complemented by fine-grained linguistic features, automatically extracted using linguistic analysis tools, to capture stylistic aspects. As a proof of concept, the analysis is performed on a corpus of 96 testimonies in Spanish describing two robbery cases. The results suggest that both mental reconstruction and narration times positively impact the accuracy of testimonies, as inaccuracies predominantly involve peripheral details. Furthermore, while the study confirms that educational level affects testimony quality, no significant differences were observed in the frequency of erroneous reports. This study contributes to the understanding of the relationship between cognitive strategies and the accuracy of witness statements, proposing an analysis approach applicable to forensic psychology for witness assessment.

Received: 17 January 2025 Revised: 29 January 2025 Accepted: 1 February 2025 Published: 8 February 2025

**Citation:** Solà-Sales, S.; Alzetta, C.; Moret-Tatay, C.; Dell’Orletta, F. When Time Matters: Exploring the Impact of Recall Techniques and Educational Levels on Witness Testimony Quality. _Information_ **2025** , _16_ , 122. https:// doi.org/10.3390/info16020122

**Copyright:** © 2025 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/ licenses/by/4.0/).

**Keywords:** mental reinstatement of context; free recall; eyewitness testimonies; automatic linguistic analysis; content analysis

# **1. Introduction**

Memory is a complex cognitive process that involves different phases, such as the encoding, storage, and retrieval of information [1]. These phases do not operate in isolation but interact with and are influenced by other cognitive processes, such as language, attention, and interpretation [2,3]. As a result, studying the interplay between memory and language is particularly relevant in forensic psychology, where it supports the evaluation of testimony quality.

The quality of a testimony is evaluated mainly in terms of its accuracy, which reflects the degree to which a testimony aligns with reality [2,4]. The alignment between testimony and what was recorded in memory can be influenced by various factors, including those related to the event, the witness, and the methods used to elicit the testimony [5,6]. In terms of witness-related variables, research suggests that emotional state [7,8], substance use [9], or the impact of beliefs [3,10] may influence memory performance, while neither gender

_Information_ **2025** , _16_ , 122

https://doi.org/10.3390/info16020122


------------------------- PAGINA 2 --------------------------

2 of 23

nor age (within the developmental range of young to middle adulthood) has a significant impact [11]. Regarding the environment in which the statement is obtained, Mugno et al. (2017) highlight that the quality of witness statements is shaped by an interplay of cognitive, social, and communicative processes, with cognitive processes emerging as critical to the effectiveness of Mental Reinstatement of Context (MRC) [12].

MRC is a process in which witnesses engage in mental immersion in the context of the event before recounting it. This practice is grounded in the principle of specific encoding, which suggests that contextual information is stored in memory alongside the event itself [13]. Similarly, Free Recall (FR), a technique encouraging witnesses to report everything they remember, including seemingly irrelevant details, relies on active witness participation as a social dynamic and the use of detailed-response elicitation as a communicative strategy. Based on the literature, these cognitive, social, and communicative strategies may collectively improve the accuracy of witness testimony [14,15].

Sociodemographic variables are widely recognized for their influence on witness testimony [16]. While variables such as age or gender have often been prioritized in related research [17,18], the role of education on testimony quality has sometimes been overlooked despite its impact on verbal and memory skills [19]. Based on the current literature, it is unclear whether education directly improves cognitive skills, if individuals with better cognitive performance are more likely to have access to advanced education, or if a third variable mediates this process [20]. One hypothesis that addresses the first possibility is the concept of cognitive reserve, which refers to the ability to maintain or optimize cognitive performance despite increased task demands, applicable to both healthy individuals and those with brain damage [21]. Furthermore, the effect of education appears to vary depending on factors such as specific cognitive abilities, years of training [22], and the complexity of the tasks involved [23].

Despite extensive research, there remains a significant gap in understanding the relationship between testimony accuracy, cognitive strategies, and individual differences [1,6,24,25]. This study aims to explore the extent to which the accuracy of testimonies is influenced by two specific cognitive strategies: the time spent on mental reconstruction of context and Free Recall (RQ1). Additionally, the study examines the impact of the witnesses’ educational levels on testimony accuracy (RQ2). To achieve these goals, we propose combining information acquired from manual annotation of testimony content with linguistic information, capturing the narrative style, acquired using tools for automated linguistic analysis. While content information is commonly considered by forensic psychologists when evaluating testimony accuracy (see, for instance, the principles underlying the CBCA model [26,27] discussed in Section 2.4), the use of stylometric features to capture narration style for testimony assessment is relatively more recent. This approach is based on the premise that, since testimonies are conveyed through narratives, linguistic cues can be effectively leveraged to detect deception [28–31]. This principle was applied to various types of potentially deceptive texts, such as online reviews [32], news articles [33], tweets [34], and court hearings [35]. Among the earliest tools used in testimony analysis was the Linguistic Inquiry and Word Count (LIWC) software [36], which helped identify linguistic patterns associated with deception [31,35,37]. More recently, large language models have also been explored for this purpose [38].

By analyzing the relationship between testimony accuracy, narration style, and content information, this work is aimed at testing two main hypotheses. We hypothesize that a longer duration in the reconstruction and narration processes would result in an improvement in the quality of testimony, as measured by linguistic, lexical, and content indicators (HP1). Additionally, we predict a positive relationship between higher education levels and MRC and FR times and testimony quality (HP2). We test our hypotheses and analytical


------------------------- PAGINA 3 --------------------------

approach on a corpus of 96 testimonies describing two robbery cases, collected as part of a research study. While modest in size, the corpus holds value for our purposes, as it was carefully developed under the supervision of forensic psychologists and manually annotated by experts in testimony assessment for a set of fine-grained content information. This unique and high-quality dataset serves as an ideal proof of concept for our method and it is suitable to provide preliminary evidence to verify our hypotheses.

This research has broad relevance in psychology, particularly in the legal field, where testimonies often constitute primary evidence. Specifically, this study offers the following contributions: (i) a mixed-method approach to analyze testimony quality; (ii) a preliminary investigation into the relationship between MRC and FR times, testimony accuracy, and narration style; and (iii) initial evidence on the impact of a witness’s educational level on the quality of details in testimonies.

# **2. Materials: The Corpus of Testimony**

## _2.1. Research Study Participants_

To ensure a diverse sample, a call for participation was disseminated through social networks between March and May 2022, allowing interested candidates to contact the researchers directly. The university overseeing the study, along with its code of ethics, was explicitly mentioned in the announcement. This strategy facilitated the inclusion of the general population, providing an accessible and wide-reaching recruitment method.

The inclusion criteria required participants to be native Spanish speakers without any known linguistic, memory, or attention-related impairments. Additionally, participants had to be between the ages of 18 and 65, in accordance with the age range criterion established by [5].

A group of 48 volunteers took part in the research study carried out to collect testimonies. The selection of participants aimed to achieve an equitable distribution across key sociodemographic factors, resulting in a balanced sample. The sample is balanced in terms of gender (24 males, 24 females) and age, with participants ranging from 18 to 63 years old (AVG = 38.87; SD = _±_ 12.7).

The study was conducted entirely in Spanish within the Valencian Community, where both Castilian Spanish and Valencian hold official language status. Consequently, all participants reported fluency in both languages, with 20.83% identifying Valencian as their mother tongue, 12.5% identifying Castilian Spanish as their mother tongue, and 66.67% indicating equal proficiency in both.

**Education Level.** Education was classified into four levels, following the Spanish education system. The most basic level, _compulsory schooling_ , is typically completed by the age of 16 and includes primary and secondary education, both of which are mandatory in Spain. _Non-Compulsory Preparations_ encompass the Spanish Baccalaureate (two optional years of high school required for university admission) or vocational training aimed at acquiring professional skills. _higher education_ refers to completing a bachelor’s or master’s degree at a university, while the final level, _post-university_ , includes obtaining a doctorate or a post-university master’s program.

Participants were grouped into these categories according to the highest level of education they had achieved at the time of the interview. The sample was distributed as follows: 25% completed compulsory schooling, 31.25% Non-Compulsory Preparations, 20.83% higher education, and 22.91% post-university education.

## _2.2. Corpus Creation Procedure_

The study consisted of two sessions supervised by a team of forensic psychologists, with the initial session focused on gathering sociodemographic information, verifying inclusion criteria,


------------------------- PAGINA 4 --------------------------

and having participants read and sign ethical documentation. In the second phase, an interview lasting about 30 min was conducted fully in Spanish and audio-recorded.

The interview consisted of reading two crime stories adapted from Tucker (2019) [39], which are grounded in the research conducted by Helm et al. (2016) [40], and narrating them following the recommendations of the Cognitive Interview to improve recall. The stories, originally written in English, report a robbery and consist of about 140 words. The stories were translated into Spanish and adapted to a Valencian context to enhance participants’ identification with the events by incorporating culturally and contextually familiar scenarios. As participants had no prior exposure to the original English versions, any potential misalignments in translation did not influence their responses. Both stories were complemented by 4 images portraying the key characters: a robber, a victim, and two intervening individuals who come to help the victim. The two stories differ in the character’s physical attributes, the spatiotemporal context, and the modus operandi of the robbery. These narratives were previously used in a study that successfully examined deception detection based on linguistic variations in trial testimonies [41].

After reading each of the two stories, participants were instructed to engage in Mental Reinstatement of Context (MRC) by mentally reconstructing the narrative, immersing themselves in the event, and reflecting on its emotional and contextual aspects. They were encouraged to proceed at their own pace, with the option of closing their eyes to increase concentration. Participants indicated verbally to the interviewer when they felt they had completed the task and the experimenter measured the time allocated to MRC.

Following the MRC task, participants narrated the story as if testifying as witnesses in a crime trial. They were explicitly instructed to recount the events with maximum accuracy. The time each participant spent narrating the events was documented as Free Recall (FR) time. Both the MRC and FR times were recorded as independent variables for the study.

The experimenter also manually transcribed the 96 testimonies, obtaining the study corpus. Natural punctuation [42] (i.e., periods and commas) were added according to speech pauses and intonations to identify major utterance boundaries, roughly corresponding to sentences.

## _2.3. Ethical Considerations_

The research was conducted with human participants and adhered to ethical review, obtaining approval from the UCV/2021-2022/060 ethics committee. The approval endorses compliance with the guidelines established in the Helsinki Declaration. Several documents were included, such as the Participant Information Sheet, which details the study and highlights the absence of financial compensation, Personal Data Protection, informed consent, and the Consent Withdrawal Form.

Note that personal data from voluntary participants were securely stored and accessible only to the researchers involved in the data collection phase. Furthermore, the participants’ identities were anonymized using alphanumeric codes linked to their data.

## _2.4. Corpus Annotation_

The corpus of testimonies was annotated at two complementary levels. The first level regards the linguistic properties of the text, i.e., syntax and morphosyntax. Several studies have highlighted how linguistic style features, such as the use of pronouns, negative adverbs, prepositions, and conjunctions, can be linked to behavioral and emotional outcomes [31]. Building on this premise, prior research has shown that verbal cues are often correlated with deception and truth-telling (see, among others, refs. [28,35,41,43–45]). Most of these studies have focused on English-language statements, revealing that deceptive sentences tend to be syntactically simpler. This reduced complexity likely reflects an effort


------------------------- PAGINA 5 --------------------------

to minimize the cognitive load associated with fabricating a credible false narrative and to facilitate recalling lies [35,46]. Additionally, deceptive texts often contain a higher frequency of verbs and personal pronouns, while truthful texts typically feature more nouns, adjectives, and prepositions [44]. Research in other languages supports these findings, while also uncovering language-specific patterns. For instance, in Spanish, ref. [47] identified that false reports are often characterized by the absence of reflexive pronouns, negations, and common nouns, as well as by generally shorter sentences. Similarly, ref. [48] found that truthful accounts frequently include a higher occurrence of first-person verbs in past and future tenses, sensory-perceptual terms, insight words (e.g., “think”), tentative expressions (e.g., “maybe”), and exclusive words (e.g., “but”). In contrast, deceptive texts exhibited shorter responses in second- and third-person forms and included words associated with negative emotions. These patterns suggest that deceptive statements, regardless of the language, tend to adopt a more impersonal tone, creating emotional and psychological distance from the events being described. Furthermore, they reveal the importance of considering fine-grained linguistic traits when assessing the quality of testimonies.

To acquire the linguistic properties relevant to testimony quality assessment, we account for morpho-syntactic properties automatically extracted from the testimonies using Profiling-UD [49]. The tool first parses the plain texts to automatically acquire their underlying morpho-syntactic structure. Parsing is carried out by the tool relying on UDPipe [50], a pipeline which carries out basic pre-processing steps, i.e., sentence splitting and tokenization, POS tagging, lemmatization, and dependency parsing, with an accuracy in Spanish of around 92%. Then, the Profiling-UD tool automatically extracts approximately 150 features, either at the sentence or document level, derived from raw, morpho-syntactic, and syntactic levels of linguistic representation. The exact number of features extracted from a given text or sentence can vary slightly based on the specific content. In this instance, for example, the tool yielded 125 features extracted from the corpus of testimonies at the document level. The features acquired using the tool are detailed in Table 1. These linguistic characteristics help define language variation within and across texts, reflecting the stylometric properties of testimonies [49,51,52], which, as we discussed above, are highly predictive of testimony quality.

**Table 1.** Linguistic indicators at document (testimony) level aggregated by group.

|**Linguistic Feature**<br>**Label**|
|---|
|**Raw Text Properties (****_Raw Text_)**<br>Average document length<br>n. tokens, n. sentences<br>Average sentence length<br>tokens per sentence<br>Average word length<br>charactersper token|
|**Vocabulary Richness (****_Lexical Variety_)**<br>Type/token ratio for words and lemmas<br>TTR (form), TTR (lemma)|
|**Morpho-syntactic information (****_Part of Speech_)**<br>Distribution of POS<br>[UD pos tag]<br>Lexical density<br>lexical density|
|**Syntactic Relations (****_Syntactic Deps_)**<br>Distribution of dependency relations<br>[UD dependency tag]|


------------------------- PAGINA 6 --------------------------

**Table 1.** _Cont._

|**Linguistic Feature**|**Label**|
|---|---|
|**Global and Local Parsed Tre**<br>Average depth of the whole syntactic tree<br>Average and maximum dependency<br>link lengths<br>Average length of the maximum<br>dependency links in document<br>Average number of prepositional chains<br>per sentence<br>Average length of prepositional chains<br>and distribution by depth<br>Average clause length|**e Structures (****_Tree Structure_)**<br>Tree depth<br>link length (avg), link length (max)<br>link length (avg,max)<br>n. prepositional chains<br>prep. chain len. (avg), prepositional<br>distr. (n)<br>tokensper clause (avg)|
|**Order of Elem**<br>Relative order of subject and object with<br>respect to the verb|**ents (****_Order_)**<br>Subject pre/post-verbal, object<br>pre/post-verbal|
|**Inflectional Morphol**<br>Inflectional morphology of lexical verbs<br>and auxiliaries<br>**Verbal Predicate Stru**|**l ogy (****_Verb Inflection_)**<br>Verbs/aux (tense/mood/num, pers/form)<br>**cture (****_Verb Predicate_)**|
|Distribution of verbal heads per sentence<br>Verb arity and distribution of verbs<br>byarity|verbal head per sent<br>verb edges (n./avg)|
|**Use of Subordination (**<br>Distribution of principal and<br>subordinate clauses<br>Average length of subordination chains<br>and distribution by depth|**_Subordinate Strucutre_)**<br>princ. proposition distr., subord.<br>propositions distr.<br>subord. chain len. (avg), subordinate<br>distr. (n)|
|<br>Relative order of subordinate clauses with<br>respect to the principal proposition|<br>subordinate (pre/post)|

The further level of annotation delved into the content of the testimonies. This annotation was carried out by experts in forensic psychology using a novel set of XML-style tags rooted in [27,53] revisions of the Criteria-Based Content Analysis (CBCA) model. CBCA considers qualitative features of testimonies to assess their credibility, including the structure of the account, references to time and places, presence of details, reported dialogues, and emotional involvement. The model assumes that truthful testimonies are more likely to contain these elements due to the genuine cognitive and emotional processes involved in recalling real events. Table 2 reports the overview of the annotation schema, which encompasses three main groups: cognitive and motivational factors, and memory errors. The selection of these specific criteria was made based on their broad acceptance within the field of psychology in the context of testimony, as well as their suitability for achieving the study’s objectives.

Regarding cognitive processes, script-deviant information involves the annotation of superfluous details, unnecessary for understanding the main event, such as the taste of the witness’s ice cream. The annotation of episodic autobiographical memory, as per the original schema by [53], encompassed spatial–temporal coordinates of the events and sensory perception details (e.g., _I noticed a movement_ ). This study expanded this category to include information about the characters’ physical appearance, acknowledging its relevance in robbery testimonies. Additionally, explicit references to the witnesses’ thoughts, emotions, and attributions related to the perpetrator’s mental state were incorporated into this


------------------------- PAGINA 7 --------------------------

category, consolidating the “Emotions and Feelings”, “Own Thoughts”, and “Attribution of Perpetrator’s Mental State” classes from the schema of [53].

**Table 2.** Content indicators aggregated by group.

|**Feature Type**|**Tagged Content**|
|---|---|
|Script-deviant information<br>Episodic autobiographical me|**Cognitive Criteria**<br>Superfluous details.<br>mory<br>Spatial information, temporal information,<br>mental state information, sensory impressions,<br>andphysical descriptions.|
||**Motivational Criteria**|
|Admitting lack of memory<br>Spontaneous corrections|Forgetfulness introduced by expressions such as<br>‘I don’t know’ or ‘I don’t remember’.<br>Self-correction or the addition of details without<br>prompt bythe interviewer.|
||**Memory Errors**|
|Distortion errors|A detail of the story reported incorrectly.|
|Commission errors|False information originally not in the story.|

Motivational criteria, on the other hand, encompass cases of strategic self-presentation. These include cases where witnesses express uncertainty or admit a lack of knowledge (e.g., “I don’t remember her hair color”) and instances of spontaneous self-corrections during narration.

The final category of annotated information focuses on comparisons between testimonies and the original narrative. This comparison enables an assessment of testimony accuracy by calculating the ratio of correct information to total reported information [25]. Memory errors are broadly categorized into two main types, distortions and commissions, following the classification proposed in previous research [24,54,55]. Distortion errors occur when the witness reports modifications or alterations to existing story elements. Commission errors capture cases where entirely new elements, not part of the original story, are introduced, whether they are relevant or marginal details. The memory error annotations were conducted by two experts, achieving an agreement rate of approximately 94%, demonstrating the reliability of the annotations.

# **3. Results**

## _3.1. Mental Reinstatement and Free Recall_

In this section, we present the results of quantitative and qualitative analyses conducted to evaluate the quality of testimonies. The analyses are focused on two dimensions: MRC, namely the time dedicated by participants in the study to the mental reconstruction of their stories; and FR, i.e., the time spent narrating them. We aim to understand how the time-related aspects of these processes influence the accuracy of the testimonies. To carry this out, we illustrate how stylometric and content-related indicators within the testimonies can be monitored to evaluate testimony quality and present the results of our proposed methodology on the testimony corpus presented in Section 2.

Figure 1 displays the seconds employed by each participant for the MRC and FR tasks during the research study. Concerning MRC, on average, participants required 13.5 s to mentally reconstruct the events. In general, the majority of participants (54.64%) performed MRC in 10 s or less. Conversely, only a small minority (16%) took more than 20 s, and none exceeded the 50 s mark in this regard. Concerning FR times, Figure 1 displays that narration times are consistently higher than MRC times. On average, participants spent 46.56 s on


------------------------- PAGINA 8 --------------------------

the narration process. Notably, a substantial majority of participants (81%) were able to convey the entire story within a minute. These times align with the average reading time of the stories, which is 49.37 s.

The graph in Figure 1 indicates a potential relationship between the two temporal variables, which we recommend to further explore through statistical measures such as Spearman correlation analysis ( _ρ_ ) between MRC and FR. The analysis performed on our corpus reveals a statistically significant, in terms of _p_ -value ( _p_ ), moderate correlation ( _ρ_ = 0.469, _p <_ 0.001) between these temporal variables. However, some participants exhibited extended FR times despite relatively shorter MRC durations. This observation provides insight into why the correlation is classified as medium rather than strong.

**Figure 1.** Time employed during the Mental Reinstatement of Context (blue) and Free Recall (red) processes by each participant in the study.

## 3.1.1. Impact on Narration Style

Correlation analysis can be used to examine whether the duration of mental reinstatement and narration influences the linguistic properties of testimonies. Specifically, Spearman’s rank correlation is used as it is well suited to assessing monotonic relationships between variables. This method enables one to determine whether higher values of the temporal variable correspond to higher (positive correlation) or lower (negative correlation) values of the linguistic features under consideration.

The results of this analysis on the corpus of testimonies are reported in full in Appendix A. Our findings reveal that only a subset of linguistic features demonstrates a significant correlation with the temporal variables: 38.26% of the features correlate with Free Recall, while 26.95% correlate with Mental Reinstatement of Context. Among these features, those related to the length of the testimonies emerge as the most strongly correlated with both temporal metrics. Specifically, MRC times correlate _ρ_ = 0.61 with the number of tokens in the testimonies and _ρ_ = 0.44 with the number of sentences (both _p <_ 0.001). Notably, the correlation results are even more robust when examining narration times: _ρ_ = 0.83 with the number of words in the narrative and _ρ_ = 0.76 with the number of sentences. Additionally, a significant positive correlation ( _ρ_ = 0.51 with MRC and _ρ_ = 0.71 with FR, _p <_ 0.001 for both) is observed with lexical variety, assessed as the ratio of different words to the total number of words in a text (type-token ratio metric, TTR).

Delving into features capturing deeper morpho-syntactic properties, time significantly impacts the overall structure of the dependency tree. Features such as the length of dependency links and the number of prepositional chains within sentences exhibit a moderate yet significant correlation with MRC and FR (see Appendix A). The higher


------------------------- PAGINA 9 --------------------------

linguistic complexity of narratives with longer narration times may arise from the increased use of coordinated structures and modifiers, particularly adjectives. Content analysis of the manually annotated elements will determine whether this complexity aligns with a greater density of informational content.

Remarkably, the linear order of core sentence elements (subjects and objects) in relation to the dependent verb remains unaffected by FR and MRC times. Conversely, an interesting observation emerges regarding the inflection of verbs and auxiliaries. While MRC does not seem to impact verb inflection, FR time does, particularly concerning the use of the present tense and the person of the verb. This suggests that higher FR times may be associated with more instances where the participant interjects themselves into the narration using expressions like “I don’t remember”, “I think”, or “I believe”.

## 3.1.2. Cognitive and Motivational Criteria Analysis

The analysis of manual annotation enables one to measure the impact of MRC and FR times on the content information reported in the retellings.

As a proof of concept, we analyzed the retellings of our corpus and their manual annotation. We counted 1078 tags in the corpus, namely 1041 cognitive and 37 motivational criteria tags. This analysis highlights a large disparity between the two categories, with cognitive criteria vastly outnumbering motivational criteria. As shown in Figure 2, this difference underscores the dominant presence of cognitive elements within the testimonies, reflecting their central role in the narrative structure and content of the participants’ accounts. This is not surprising considering that cognitive criteria encompass tags related to the typical information found in eyewitness testimonies, such as actions, spatial and temporal information, the emotions of the witness, and the appearance of the people involved in the events. Among the content criteria, the most frequently occurring tags refer to the spatiotemporal coordinates of the events and the physical appearance of the people involved in the robbery. Notably, information identified by experts as superfluous to the dynamics of the crime was frequently reported in the retellings. The remaining content criteria tags, referring to the participants’ feelings and perceptions, cover a marginal distribution of 2.13%. Among the motivational criteria, tags capturing expressions of forgetfulness emerge as the most frequent, although their overall distribution remains relatively low.

**Figure 2.** Frequency distribution as a percentage of tags used to annotate the retellings, grouped by category.


------------------------- PAGINA 10 --------------------------

To complement the quantitative findings and provide a deeper understanding of the linguistic and content dimensions of the annotation, we conducted a lexical analysis of the expressions marked with tags. This involves examining the frequency of the words and phrases annotated by the experts and analyzing their distribution across the retellings in the corpus. By identifying patterns and variations in the annotated lexical items, this analysis aims to uncover insights into how specific linguistic elements contribute to the overall narrative structure and testimony quality.

The results align with the tag distribution analysis. Specifically, expressions tied to spatial and temporal aspects, such as “ _calle_ ” (street), “ _detrás_ ” (behind), and “ _de repente_ ” (suddenly), were most frequently identified. Similarly, physical descriptions were notably frequent in the annotations. The descriptions of individuals involved in the events suggested a clear intention of witnesses to characterize the perpetrators of the crime. Specifically, the terms found in the retellings indicated a focus on details related to hair, ethnic features, and physical build, emphasizing the witnesses’ emphasis on portraying key aspects of the individuals. Regarding superfluous details, the most frequently appearing words were “friend” and “ice cream”, associated with the witness’s plans with her friend and their activity during the incident.

A further stage of content analysis delved into the relationship between MRC and FR times and the annotated tags. The outcomes of this correlation analysis on our corpus, outlined in Table 3, reveal several significant patterns. Primarily, a substantial and positive correlation was evident between cognitive and motivational tags and both time variables ( _ρ_ = 0.55, _p <_ 0.001 for MRC; _ρ_ = 0.84, _p <_ 0.001 for FR). However, upon closer inspection, it appears that, for MRC, these results are predominantly influenced by cognitive criteria, as motivational criteria exhibit a significant correlation exclusively with FR times. Notably, the correlations are more robust when considering Free Recall times for almost all tags, indicating that, as narrative time increases, cognitive and motivational details tend to rise, with a more pronounced impact on cognitive details compared to motivational ones.

**Table 3.** Spearman correlation scores ( _ρ_ ) and _p_ -values ( _p_ ) between tags and MRC and FR durations. The table also reports the average number of tags present in each retelling of the corpus with standard deviation (column ‘Avg/narr (SD)’).

|**Tag**|**MRC****_ρ_**(**_p_**)|**FR****_ρ_**(**_p_**)|**Avg/Narr (SD)**|
|---|---|---|---|
||**Cognitive Criter**|**ia**||
|Spatial information|0.55 (_<_0.001)|0.52 (_<_0.001)|3.27 (_±_1.87)|
|Temporal information|0.21 (0.04)|0.46 (_<_0.001)|2.09 (_±_1.49)|
|Sensory impression|0.26 (_<_0.001)|0.32 (0.001)|0.19 (_±_0.51)|
|Physical description|0.29 (_<_0.001)|0.68 (_<_0.001)|2.27 (_±_3.39)|
|Mental state|_−_0.06 (0.59)|0.09 (0.41)|0.05 (_±_0.22)|
|Superfluous detail|0.4 (_<_0.001)|0.46 (_<_0.001)|2.97 (_±_1.99)|
|All Cognitive|0.56 (_<_0.001)|0.82 (_<_0.001)|10.84 (_±_6.47)|
||**Criteria**|||
|Spontaneous correction|0.07 (0.49)|0.18 (0.08)|0.1 (_±_0.37)|
|Lack of memory|0.04 (0.69)|0.45 (_<_0.001)|0.28 (_±_0.54)|
|All Motivational|0.06 (0.59)|0.44 (_<_0.001)|0.39 (_±_0.7)|
|Cognitive and Motivational|0.55 (_<_0.001)|0.84 (_<_0.001)|11.23 (_±_6.73)|

## 3.1.3. Memory Error Analysis

Memory errors refer to discrepancies between reported testimonies and actual events. When the facts are definitively known, such as through a reliable external testimony or,


------------------------- PAGINA 11 --------------------------

as in our corpus, when the events originate from predefined stories, a comparative analysis can be conducted between the original stories and participants’ retellings. This analysis specifically targets tags annotated as episodic autobiographical memories (see Table 2). A testimony’s accuracy is determined as the ratio of correct information encoded within these tags to the total amount of information (including relevant as well as superfluous details) marked as both correct and incorrect [25,54]. By systematically examining the content of each participant’s retelling and comparing it with the original details, this approach enables the identification of discrepancies, such as omissions, distortions, or commissions, and quantifying the extent and nature of memory errors. Through this analysis, we aim to deepen the understanding of the accuracy and reliability of participants’ episodic memory recall, shedding light on the mechanisms underlying memory reconstruction.

When performing the analysis on our corpus, we noticed that participants’ narratives exhibit a high level of accuracy, with correct information reported in 93% of cases. Specifically, we identified 77 instances of tags where the information did not align with the content of the original story. Among these, experts identified 53 cases as distortion errors (i.e., proper mistakes), with the remaining classified as commission errors (namely, instances of made-up information). Notably, these errors were predominantly associated with non-essential details, such as superfluous information in the narrative, rather than critical elements like temporal or spatial information.

## _3.2. Education-Level Impact_

While testimonies from witnesses with higher education levels are often involved in trials as they provide legally relevant knowledge to the court based on their area of expertise [56], the specific ways in which the education level influences the quality and style of a testimony remain underexplored. Conducting a correlation analysis between this sociodemographic variable and the linguistic traits of testimonies can offer valuable insights into how education level impacts narrative style. Furthermore, correlating education level with manually annotated tags can provide a deeper understanding of its influence on the overall quality of the testimony.

We conducted the analysis on our corpus relying on the Kruskal–Wallis non-parametric test ( _χ_ ). We chose this test because it is suitable to compute correlations on multiple groups, as in this study we grouped participants on the four levels of education described in Section 2.1: compulsory schooling (B), Non-Compulsory Preparation (HP), higher education (U) and post-university (PU).

For both reconstruction and narration times, the test indicated that there is a significant difference between the four groups (FR time: _χ_<sup>2</sup> (3) = 18.19, _p <_ 0.001; MRC time: _χ_<sup>2</sup> (3) = 12.59, _p_ = 0.006). The post hoc Dunn’s test using a Bonferroni-corrected alpha of 0.0083 indicated that the mean ranks are significantly different between the PU and the B and HP groups concerning FR, and between the PU and the HP group for MRC times. Upon examining the average MRC and FR times for each group, we observed a trend where both times tend to increase with higher levels of education. Consider Figure 3, which illustrates a proportional increase in FR time corresponding to higher education levels. In particular, participants with post-university education are the group dedicating more time to narrating and mentally reconstructing stories compared to those with lower levels of education. Notably, MRC times follow a similar trend to FR times, albeit with a less pronounced tendency. In fact, except for the post-university group, the other groups tend to dedicate a comparable amount of time to MRC.

The Kruskal–Wallis test, conducted on linguistic features across different educationlevel groups, enables the exploration of the stylistic variations in the narratives of participants based on their education level. The detailed results are available in Appendix B. Upon


------------------------- PAGINA 12 --------------------------

conducting the analysis, notable differences emerged across various dimensions among the four groups. Particularly prominent is the observed increase in the number of tokens in retellings by participants with higher levels of formal education. Group B (compulsory schooling), on average, produced narratives with 57.98 words, while the post-university group presented narrations with double the word count (106.02), accompanied by longer sentences (18.07 words per sentence on average in B, 20.56 in PU). This discrepancy extends its influence to various linguistic traits. The higher the education level, the higher the lexical variety the retellings exhibit, as well as an increased syntactic complexity. This complexity manifests on multiple levels, including a larger use of subordinate clauses and modifiers, the employment of verbs and auxiliaries in the subjunctive mood, and an elevated use of post-verbal participants, a less standard construction in Spanish.

**Figure 3.** Average time spent by each education-level group on Free Recall (FR) and Mental Reinstatement of Context (MRC), along with the average number of content tags and memory errors annotated in the narratives of each group.

In terms of content analysis, the results revealed a positive trend in the number of details as the level of education increased. However, it is relevant to note that the educational background of the witness does not seem to affect the frequency of memory errors.

# **4. Discussion**

## _4.1. Main Findings_

The aim of this study was to investigate the interplay between the temporal aspects of the testimonial process and the education level of witnesses, as well as their influence on linguistic expression and the accuracy of eyewitness testimonies. Leveraging a mixedmethod approach, we delved into both quantitative and qualitative dimensions, exploring linguistic expressions and the semantic content of testimonies in relation to time and a sociodemographic variable.

The outcomes of the analyses contribute to addressing the two research questions posed in this study. In exploring our first research question, regarding the influence of cognitive strategies on testimonial quality, our findings unveil the profound impact of cognitive processes on both the content and linguistic expression of testimonies. In particular, we found significant correlations between temporal engagement and linguistic style. Regarding the second question investigated in this study, our analysis of the linguistic features of testimonies showed that as education level increases, retellings become more


------------------------- PAGINA 13 --------------------------

lexically varied and syntactically complex. Finally, errors usually appear as changes to the original events rather than the creation of new information. Below, we address each finding in more depth.

## _4.2. Impact of Cognitive Strategies_

Regarding RQ1, concerned with variations in testimony quality induced by cognitive processes, it was hypothesized that lengthier MRC and FR times would enhance the accuracy of testimony, measured through linguistic and content indicators (HP1). As a first result, we observed a positive correlation between these two variables, noting that individuals who reinstated the context for a longer period also dedicated more time to the testimonial narration, possibly introducing a higher amount of relevant information.

Our analysis then moved to exploring the impact of MRC and FR durations on the linguistic style of testimonies. The correlation between the linguistic properties of the text and reconstruction and narration durations reveals that the time individuals spend mentally reconstructing events exerts a substantial influence on linguistic style. Specifically, longer duration in the reconstruction and narration processes results in higher linguistic complexity of the testimony, as captured by a more diverse vocabulary, a higher number of words and sentences, and greater use of coordinated constructions and modifiers. These results appear to confirm HP1, namely that longer reconstruction and narration durations result in an improvement in the quality of testimonies, as measured by linguistic and lexical indicators. This result is also in line with the related literature, which found that truthful statements tend to be syntactically more complex than deceptive ones (see Section 2.4).

While the variations in linguistic phenomena with narration time were anticipated, as longer stories inherently contain a greater richness of linguistic elements, the correlation with reconstruction times presents a more unexpected and compelling result.

Additionally, our findings point to a positive correlation between the duration of the FR and MRC processes and the overall presence of content cues in the statements. This result is consistent with previous research, which suggests that a combination of both techniques is effective in improving recall, compared to the use of the other components of Cognitive Interview [15]. In particular, the results derived from lexical analysis identified spatiotemporal and superfluous details as the most commonly mentioned in the retellings. The prevalence of spatiotemporal details aligns with established theories on human memory, which posit that our memory system is inherently designed to link information about events to the spatiotemporal context in which the information was encountered [57]. As for the physical descriptions, the witnesses concentrated mainly on hair, ethnicity, and complexion when describing the individuals who participated in the robbery. Regarding motivational content, several factors may explain the limited presence of these tags in the testimonies. Firstly, performing FR and MRC techniques may reduce memory gaps and spontaneous corrections in the retellings, potentially diminishing the need for motivational elements to fill in missing details. Secondly, the annotation process specifically focused on a subset of motivational criteria from the CBCA model, inherently narrowing the scope and providing a partial view of the broader phenomenon.

The enhanced quality of testimony attributed to the use of the MRC technique in the process of retelling events is supported by cognitive theories of memory, particularly the encoding specificity hypothesis [13]. This hypothesis asserts that information retrieval is most effective when the retrieval context closely mirrors the context in which the information was encoded. The MRC technique relies on this principle by reinstating the original context, thereby enhancing the overlap between encoding and retrieval cues, which facilitates access to stored memories [58,59]. This mechanism has also been explored at the neural level, supporting the hypothesis of cortical reactivation, wherein the cortical


------------------------- PAGINA 14 --------------------------

patterns active during the encoding phase are reactivated during memory retrieval [60,61]. Moreover, the observed relationship between MRC performance and testimony quality may be mediated by cognitive abilities, such as the capacity to mentally travel back in time or vividly re-experience past events [6]. These findings highlight the multifaceted benefits of the MRC technique in improving the quality and richness of testimonies.

Upon reviewing the accuracy rate, our results align with previous works such as [25,62]. Furthermore, we noted a higher frequency of distortion errors than commission errors. This result indicates that individuals tended to modify the details of the original story, rather than introducing completely new, invented details. It was observed in past research that distortions and commissions potentially involve distinct psychological phenomena [63]. Continuing in this vein, reference [64] suggested that most falsehoods, whether intentional or unintentional, tend to take the form that requires the least effort, i.e., is closest to the truth. Our results appear to be aligned with these observations, indicating that distortions occur more frequently due to their higher cognitive efficiency with respect to commissions. It should be noted that distortions, in our data, typically concern marginal aspects of the narrative. This finding aligns with previous research indicating that central details tend to be more accurately recalled compared to peripheral ones, although this may be contingent upon the emphasis placed on the details during the encoding or retrieval phase [65,66].

## _4.3. Impact of Individual Differences_

Concerning RQ2, referring to the impact of sociodemographic differences on testimony quality, we addressed this issue by focusing on the education level of the participants. The results obtained seem to support the hypothesis related to educational level, suggesting that a higher level of education is associated with a longer duration of MRC and FR processes. However, while individuals with higher education levels are inclined to provide more comprehensive testimonies, they are equally prone to committing memory errors as those with lower levels of education. This relationship could be explained by the positive influence of education on cognitive skills such as memory language and attention [67]. During education, individuals encounter tasks that demand the development of cognitive abilities related to memory, but also to language, thus acquiring a larger vocabulary and a greater ability to manipulate syntax. Accordingly, the study’s findings suggest that people with a higher level of education have greater linguistic ability to communicate events. Additionally, this continuous training could lead to an increased cognitive reserve that would allow these individuals to maintain optimal cognitive performance in response to increased demand [22,68]. Consequently, the educational level could act as a protective factor [69]. However, reference [23] suggests that this effect only occurs when sufficient external information is available regarding the more efficient mnemonic strategy.

## _4.4. Limitations and Further Research_

While our study provides results that enrich the understanding of the role of cognitive factors in the accuracy of testimony, it is not without limitations. The modest size of our corpus calls for caution in generalizing findings, and future research with larger samples is warranted to enhance the robustness and applicability of our conclusions. In addition, all participants in the study are Spanish speakers, and the analysis focuses exclusively on two cases of robbery. While these factors limit the generalizability of the findings to different linguistic or cultural contexts and other types of criminal events, conducting a monolingual study provides the advantage of eliminating potential linguistic variability. This allows for more precise conclusions about the linguistic and cognitive processes at play within the specific context of Spanish-language testimonies. Moreover, focusing solely on


------------------------- PAGINA 15 --------------------------

two robbery cases was a necessary choice, as the study relied on a specialized corpus with manually annotated tags. This ensured a high level of detail and accuracy in the analysis, which would not have been feasible with other, possibly larger, corpora lacking annotation.

The study’s correlational nature limits the ability to establish definitive causal relationships, yet it still provides valuable insights into potential associations that can guide future research. Additionally, while the design does not include direct measures to confirm whether participants successfully reinstated the context as instructed, this approach maintains a more naturalistic and ecologically valid setting for data collection by excluding the use of devices to collect physiological data. Future research could address this by incorporating physiological or behavioral measures to confirm the effectiveness of context reinstatement, thereby strengthening the understanding of its role in enhancing testimony accuracy.

In addition, it is important to recognize that the laboratory context offers significant advantages, such as the ability to standardize conditions and control variables [48]. However, it is essential to interpret the results considering the differences between a simulated environment and reality. For example, the emotional impact and time spent on the statement may vary in real contexts due to the greater personal involvement in the event. Therefore, while this study focused on educational levels and specific cognitive techniques, it is essential to consider other factors that may influence eyewitness testimony, such as personality or emotional state. Further research exploring the interaction between variables in the environment in which the crime occurred, the witness, and the context in which the statement was obtained would be beneficial. In this regard, it would also be interesting to add omissions to the study of memory errors. These would enrich our understanding of the complex psychology of eyewitness testimony and help to better contextualize the findings obtained in controlled settings such as the present study.

# **5. Conclusions**

This study investigated the relationships between cognitive and sociodemographic factors, linguistic features, and memory accuracy in witness testimonies. By leveraging a corpus of retellings, annotated for content information under the supervision of forensic psychology experts and for narrative style using an NLP tool, we were able to investigate the interplay of these variables.

Our findings highlight several key aspects. The analysis confirmed the significant influence of MRC and FR durations on the linguistic complexity and information density of testimonies, aligning with cognitive theories, such as the encoding specificity hypothesis, which suggests that recalling the story context facilitates more accurate memory retrieval. Concerning narrative style, the correlation analysis between linguistic features revealed that only a subset of features are significantly associated with MRC and FR durations. This suggests that certain linguistic traits may serve as indicators of memory accuracy and testimony quality. Similarly, this study reveals that the educational background of witnesses has a significant impact on both the style and content of testimonies. Higher education levels were associated with greater linguistic complexity, suggesting that education may influence cognitive skills such as language processing and recall organization.

The use of manual annotation for fine-grained content information proved essential for this research. In this sense, the corpus, while small and monolingual, represented an essential enabling element of this research since such annotations are rarely available in existing corpora. This approach enabled us to identify nuanced patterns in testimony quality and memory errors, underscoring the importance of curated datasets in forensic research.

Overall, this study demonstrates the utility of an integrative approach combining linguistic analysis, sociodemographic factors, and cognitive theories to better understand


------------------------- PAGINA 16 --------------------------

eyewitness testimonies. Future research should aim to validate these results on larger, more diverse datasets and explore additional factors influencing testimony quality, such as stress, context, and cultural variables. Additionally, integrating physiological measures or automated tools for context monitoring could further enhance the reliability of findings.

**Author Contributions:** Conceptualization, S.S.-S., C.A., C.M.-T. and F.D.; Methodology, S.S.-S., C.A., C.M.-T. and F.D.; Software, C.A. and F.D.; Validation, S.S.-S., C.A. and C.M.-T.; Formal analysis, S.S.-S. and C.A.; Investigation, S.S.-S., C.A., C.M.-T. and F.D.; Resources, S.S.-S. and C.M.-T.; Data curation, S.S.-S.; Writing—original draft, S.S.-S. and C.A.; Writing—review & editing, S.S.-S., C.A., C.M.-T. and F.D.; Visualization, S.S.-S.; Supervision, C.M.-T. and F.D.; Project administration, S.S.-S., C.A., C.M.-T. and F.D.; Funding acquisition, S.S.-S. and C.M.-T. All authors have read and agreed to the published version of the manuscript.

**Funding:** This research was funded by the “Conselleria de Innovación, Universidades, Ciencia y Sociedad Digital”, proyecto emergente number: CIGE/2021/051, as well as Becas para la realización de estancias en el extranjero by the Universidad Católica de Valencia San Vicente Mártir, 2022.

**Institutional Review Board Statement:** The study was conducted in accordance with the Declaration of Helsinki and approved by the Institutional Review Board of Universidad Católica de Valencia San Vicente Mártir (Protocol Code UCV/2021-2022/060 and date of approval: 10 January 2022).

**Informed Consent Statement:** Informed consent was obtained from all subjects involved in the study.

**Data Availability Statement:** The original contributions presented in this study are included in the article. Further inquiries can be directed to the corresponding author.

**Conflicts of Interest:** The authors declare no conflicts of interest.

# **Appendix A. Correlation Analysis between Linguistic Features and Mental Reinstatement of Content (MRC) and Free Recall (FR)**

Spearman correlation scores ( _ρ_ ) and _p_ -values ( _p_ ) were computed between linguistic feature values and Free Recall (FR) and Mental Reinstatement of Context (MRC) times. The table includes average values (with standard deviation) for each feature in the testimony corpus.

|**Group**|**Feature**|**FR****_ρ_ (****_p_)**|**MRC****_ρ_ (****_p_)**|**Feature AVG (SD)**|
|---|---|---|---|---|
||Characters per token|0.11 (0.30)|0.12 (0.25)|4.15 (_±_0.22)|
|RawText|n. sentences|0.76 (_<_0.001)|0.44 (_<_0.001)|4.75 (_±_2.05)|
||n. tokens|0.83 (_<_0.001)|0.61 (_<_0.001)|94.18 (_±_47.85)|
||Tokens per sentence|0.26 (0.01)|0.37 (_<_0.001)|19.95 (_±_5.34)|
|Lexical|TTR form|0.69 (_<_0.001)|0.51 (_<_0.001)|0.19 (_±_0.31)|
|Variety|TTR lemma|0.71 (_<_0.001)|0.51 (_<_0.001)|0.16 (_±_0.26)|
||Lexical Density|0.17 (0.10)|_−_0.15 (0.13)|0.46 (_±_0.03)|
||Adjectives|0.51 (_<_0.001)|0.32 (0.002)|2.23 (_±_2)|
||Adpositions|_−_0.09 (0.37)|0.12 (0.26)|12.45 (_±_2.66)|
||Adverbs|0.09 (0.38)|_−_0.15 (0.15)|5.21 (_±_2.1)|
||Auxiliaries|0.17 (0.11)|0.21 (0.04)|3.42 (_±_2.16)|
||Coordinating conj.|_−_0.22 (0.03)|_−_0.18 (0.08)|6.58 (_±_2)|
||Determiners|_−_0.17 (0.09)|_−_0.02 (0.82)|12.41 (_±_2.24)|
|POS|Interjections|0.12 (0.23)|_−_0.09 (0.38)|0.01 (_±_0.06)|
||Nouns|0.05 (0.63)|0.04 (0.71)|16.28 (_±_2.3)|
||Numerals|_−_0.44 (_<_0.001)|_−_0.35 (_<_0.001)|1.68 (_±_0.91)|
||Pronouns|_−_0.16 (0.12)|0 (0.99)|8.39 (_±_2.64)|
||Proper nouns|0.12 (0.25)|0.09 (0.36)|1.76 (_±_1.23)|
||Subordinating conj.|0.2 (0.05)|0.15 (0.15)|3.02 (_±_2.08)|
||<br>Verbs|_−_0.4 (_<_0.001)|_−_0.27 (0.007)|15.27 (_±_3.06)|
||X|0.08 (0.47)|0.13 (0.20)|0.03 (_±_0.17)|


------------------------- PAGINA 17 --------------------------

|**Group**|**Feature**|**FR****_ρ_ (****_p_)**|**MRC****_ρ_ (****_p_)**|**Feature AVG (SD)**|
|---|---|---|---|---|
||Adnominal clauses<br>|0.06 (0.58)<br>|0.1 (0.32)<br>|0.24 (_±_0.59)<br>|
||Relative clauses|_−_0.02 (0.86)|0.02 (0.83)|1.71 (_±_1.42)|
||Adverbial clauses|_−_0.33 (_<_0.001)|0.02 (0.86)|2.96 (_±_1.87)|
||Adverbial modifiers|0.2 (0.05)|_−_0.16 (0.12)|4.53 (_±_2.02)|
||i<br>Adjectival modifiers|0.44 (_<_0.001)<br>|0.26 (0.01)<br>|1.7 (_±_1.53)<br>|
||Appositions|0.16 (0.13)|0.24 (0.02)|0.72 (_±_1.04)|
||Auxiliaries<br>Auxiliary passes|<br>_−_0.01 (0.89)<br>0.1 (0.33)|<br>0.13 (0.21)<br>0.05 (0.65)|<br>2.23 (_±_1.77)<br>0.21 (_±_0.53)|
||<br>Case markers|<br>0.02 (0.83)|<br>0.14 (0.18)|<br>11.11 (_±_2.85)|
||Coordinating conj.|_−_0.2 (0.05)|_−_0.11 (0.27)|6.47 (_±_1.94)|
||<br>Clausal complements|0.4 (_<_0.001)|0.15 (0.15)|0.71 (_±_0.89)|
||Conjunctions<br>|0.04 (0.70)<br>|0.01 (0.95)<br>|5.22 (_±_1.85)<br>|
||Copula|0.34 (_<_0.001)|0.21 (0.04)|0.94 (_±_1.27)|
|Syntactic|Clausal subjects|029 (0004)|014 (018)|005 (_±_023)|
|Dep|<br>Determiners|. .<br>_−_0.17 (0.10)|. .<br>_−_0.02 (0.88)|..<br>12.42 (_±_2.23)|
||Fixed mwe|_−_018 (008)|_−_005 (064)|104 (_±_121)|
||<br>Flat mwe|. .<br>0.15 (0.15)|. .<br>0.13 (0.20)|..<br>0.01 (_±_0.06)|
||Indirect objects|_−_0.29 (0.004)|_−_0.26 (0.009)|3.74 (_±_2.05)|
||<br>Markers|0.1 (0.34)|0.12 (0.25)|4.06 (_±_2.47)|
||Nominal modifiers|0.33 (_<_0.001)|0.28 (0.006)|3.15 (_±_2.27)|
||i<br>Nominal subjects|<br>_−_0.02 (0.83)|<br>_−_0.08 (0.45)|<br>3.53 (_±_1.89)|
||Nominal subject passes<br>i|_−_0.12 (0.23)<br>|_−_0.01 (0.91)<br>|0.06 (_±_0.33)<br>|
||Numeral modifiers|_−_0.45 (_<_0.001)|_−_0.29 (0.004)|1.6 (_±_0.91)|
||i<br>Direct objects|_−_0.34 (_<_0.001)|_−_0.3 (0.003)|7.03 (_±_2.3)|
||Oblique complements<br>Parataxis|_−_0.12 (0.26)<br>0.38 (_<_0.001)|0.07 (0.51)<br>0.16 (0.12)|5.95 (_±_2.14)<br>0.71 (_±_0.99)|
||Roots|_−_0.26 (0.01)|_−_0.37 (_<_0.001)|5.33 (_±_1.28)|
||Open clausal compl.|0.1 (0.32)|_−_0.08 (0.43)|1.31 (_±_1.3)|
||Link length (avg)|0.32 (0.002)|0.17 (0.11)|2.54 (_±_0.3)|
||<br>Tree depth (avg max)|<br>0.13 (0.19)|<br>0.3 (0.003)|<br>4.3 (_±_0.95)|
||Link length (avg max)|0.33 (0.001)|0.36 (_<_0.001)|9.39 (_±_3.19)|
||Prep. chain length (avg)<br>|0.46 (_<_0.001)<br>|0.49 (_<_0.001)<br>|0.96 (_±_0.48)<br>|
|Tree|Tokens per clause (avg)|0.34 (_<_0.001)|0.25 (0.01)|6.39 (_±_1.16)|
|Structure|<br>Link length (max)<br>n. prepositional chains|<br>0.53 (_<_0.001)<br>0.58 (_<_0.001)|<br>0.39 (_<_0.001)<br>0.42 (_<_0.001)|<br>16.04 (_±_7.86)<br>2.73 (_±_2.52)|
||<br>Prepositional distr. (1)|<br>_−_0.1 (0.33)|<br>0 (0.98)|<br>72.4 (_±_38.71)|
||<br>Prepositional distr. (2)|0.44 (_<_0.001)|0.38 (_<_0.001)|9.64 (_±_20.98)|
||Prepositional distr. (3)|0.15 (0.13)|0.28 (0.006)|1.3 (_±_4.87)|
||Object post-verbal|0.12 (0.24)|0.12 (0.25)|63.86 (_±_17.36)|
|Order|<br>Object pre-verbal|<br>_−_0.12 (0.24)|<br>_−_0.12 (0.25)|<br>36.14 (_±_17.36)|
||Subject post-verbal|0.13 (0.2)|0.16 (0.12)|14.43 (_±_23.68)|
||<br>Subject pre-verbal|_−_0.05 (0.65)|_−_0.06 (0.54)|80.36 (_±_30.13)|
||Aux form:fin|0.12 (0.23)|0.06 (0.59)|86.83 (_±_31.89)|
||i<br>Aux form:ger|<br>0.17 (0.10)|<br>0.12 (0.23)|<br>0.41 (_±_2.93)|
||<br>Aux form:inf|<br>0.11 (0.29)|<br>0.14 (0.16)|<br>1.21 (_±_4.83)|
||Aux form:part|0.01 (0.89)|0.17 (0.10)|0.09 (_±_0.85)|
||<br>Aux mood:cnd|<br>0.09 (0.39)|<br>0.11 (0.27)|<br>0.15 (_±_1.46)|
||Aux mood:ind|<br>0.1 (0.33)|<br>0.1 (0.33)|<br>87.36 (_±_32.03)|
||Aux mood:sub|0.26 (0.01)|0.18 (0.08)|1.03 (_±_5.15)|
||Aux num,pers:plur,1<br>Aux num,pers:plur,3|0.25 (0.02)<br>_−_0.01 (0.89)|0.03 (0.74)<br>0.1 (0.32)|3.42 (_±_9.78)<br>19.02 (_±_26.47)|
|Verb|<br>Aux num,pers:sing,1|<br>0.12 (0.26)|<br>0.14 (0.16)|<br>1.44 (_±_6.84)|
|Inflection|Aux num,pers:sing,3<br>A ti|0.24 (0.02)<br>03 0003|0.18 (0.08)<br>015 014|64.65 (_±_35.58)<br>51_±_3698|
||ux ense:mp<br>Aux tense:past|. (.)<br>_−_0.1 (0.33)|. (.)<br>0.05 (0.64)|(.)<br>23.54 (_±_31.6)|
||<br>Aux tense:pres|<br>0.21 (0.04)|<br>0.11 (0.28)|<br>14 (_±_27.62)|
||<br>Verb form:fin|0.08 (0.45)|_−_0.19 (0.07)|60.8 (_±_15.4)|
||i<br>Verb form:ger|<br>_−_0.07 (0.47)|<br>0.1 (0.35)|<br>16.94 (_±_8.64)|
||<br>Verb form:inf|_−_0.07 (0.51)|0.05 (0.61)|19.74 (_±_11.88)|
||Verb form:part<br>Verb mood:cnd|<br>0.36 (_<_0.001)<br>031 (0002)|<br>0.35 (_<_0.001)<br>006 (056)|<br>2.53 (_±_6.95)<br>106 (_±_32)|
||<br>Verb mood:imp|. .<br>0.09 (0.36)|. .<br>0.09 (0.36)|..<br>0.08 (_±_0.79)|


------------------------- PAGINA 18 --------------------------

|**Group**|**Feature**|**FR****_ρ_ (****_p_)**|**MRC****_ρ_ (****_p_)**|**Feature AVG (SD)**|
|---|---|---|---|---|
||Verb mood:ind|_−_0.35 (_<_0.001)|_−_0.11 (0.29)|98.03 (_±_4.83)|
||Verb mood:sub|0.16 (0.11)|0.09 (0.39)|0.83 (_±_3.66)|
||Verb num,pers:plur|0.13 (0.2)|0.08 (0.45)|0.07 (_±_0.73)|
||Verb num,pers:plur,1|_−_0.22 (0.03)|0.02 (0.86)|13.5 (_±_15.35)|
||<br>Verb num,pers:plur,3|_−_0.24 (0.02)|_−_0.25 (0.02)|22.09 (_±_15.21)|
|Verb|Verb num,pers:sing|0.24 (0.02)|_−_0.02 (0.82)|0.72 (_±_2.68)|
|Iflti|Verb num,pers:sing,1|0.52 (_<_0.001)|0.25 (0.01)|6.31 (_±_9.84)|
|nlecon|Verb num,pers:sing,2|0.09 (0.36)|0.09 (0.36)|0.08 (_±_0.79)|
||<br>Verb num,pers:sing,3|0.1 (0.31)|0.12 (0.25)|56.61 (_±_16.3)|
||<br>Verb tense:fut|0.15 (0.14)|0.13 (0.20)|0.57 (_±_2.77)|
||Verb tense:imp|0.33 (_<_0.001)|0.07 (0.50)|24.38 (_±_16.58)|
||<br>Verb tense:past|_−_0.36 (_<_0.001)|_−_0.07 (0.52)|53.24 (_±_26.35)|
||<br>Verb tense:pres|<br>0.23 (0.02)|<br>0.12 (0.26)|<br>21.82 (_±_27.42)|
||Verbal root (%)|_−_0.2 (0.05)|_−_0.07 (0.53)|93.16 (_±_11.12)|
||Verb edges (avg)|_−_0.09 (0.38)|_−_0.02 (0.87)|2.63 (_±_0.33)|
||<br>Verb edges (0)|0.02 (0.86)|0.16 (0.12)|3.34 (_±_4.85)|
||Verb edges (1)|0.01 (0.9)|_−_0.03 (0.76)|14.55 (_±_10.41)|
|Verb|Verb edges (2)|0.13 (0.2)|0.05 (0.65)|29.03 (_±_11.92)|
|Predicate|Verb edges (3)|_−_0.11 (0.29)|_−_0.04 (0.66)|29 (_±_12.97)|
||Verb edges (4)|_−_0.08 (0.42)|_−_0.11 (0.28)|17.92 (_±_11.94)|
||Verb edges (5)|0.27 (0.007)|0.31 (0.002)|4.8 (_±_5.8)|
||<br>Verb edges (6)|_−_0.05 (0.61)|_−_0.07 (0.48)|1.37 (_±_3.19)|
||Verbal heads per sent|0.05 (0.6)|0.14 (0.17)|3.21 (_±_1)|
||subord. chain len. (avg)|0.08 (0.42)|0.25 (0.01)|1.22 (_±_0.26)|
||principal prop. distr.|_−_0.08 (0.41)|_−_0.16 (0.11)|43.03 (_±_14.33)|
||subordinate distr. (1)|_−_0.05 (0.6)|_−_0.22 (0.03)|81.19 (_±_19.63)|
||subordinate distr. (2)|0.1 (0.32)|0.21 (0.04)|16.01 (_±_17.75)|
|Subord|subordinate distr. (3)|<br>0.07 (0.5)|<br>0.12 (0.24)|<br>2.45 (_±_8.38)|
||subordinate distr. (4)|0.09 (0.4)|0.12 (0.26)|0.36 (_±_2.1)|
||subordinate post|_−_0.18 (0.09)|_−_0.17 (0.10)|89.05 (_±_23.03)|
||subordinate pre|0.18 (0.09)|0.17 (0.10)|10.95 (_±_23.03)|
||subordinate prop. distr.|0.08 (0.41)|0.16 (0.11)|56.97 (_±_14.33)|

# **Appendix B. Correlation Analysis between Linguistic Features and Participants’ Education Level**

The following shows Kruskal–Wallis test scores ( _χ_ ) comparing linguistic features that vary significantly among all four participant groups based on education level (B: basic level; HP: higher preparation; U: university; PU: post-university). The table includes average values (with standard deviation) for each feature in each group. Significance levels:

|||||**Average V**|**alues (SD)**||
|---|---|---|---|---|---|---|
|**Group**|**Feature**|**_χ_ (****_p_)**|**B**|**HP**|**U**|**PU**|
||Characters per token|26.88 (_<_0.001)|4.11 (_±_0.27)|4.11 (_±_0.26)|4.27 (_±_0.25)|4.22 (_±_0.22)|
|RawText|n. sentences|55.95 (_<_0.001)|3.29 (_±_1.6)|3.11 (_±_1.36)|3.75 (_±_1.71)|5.2 (_±_2.44)|
||n. tokens|70.3 (_<_0.001)|57.98 (_±_31.58)|59.63 (_±_29.12)|77.76 (_±_40.84)|106.02 (_±_53.9)|
||Tokens per sentence|17.55 (_<_0.001)|18.07 (_±_5.46)|20.18 (_±_7.3)|21.15 (_±_6.23)|20.56 (_±_4.77)|
|Lexical|TTR form|35.7 (_<_0.001)|0.04 (_±_0.16)|0.05 (_±_0.18)|0.15 (_±_0.28)|0.23 (_±_0.33)|
|Variety|TTR lemma|35.31 (_<_0.001)|0.03 (_±_0.13)|0.05 (_±_0.16)|0.13 (_±_0.24)|0.2 (_±_0.27)|
||Adjectives|15.94 (0.001)|3.04 (_±_2.83)|2.51 (_±_2.66)|3.81 (_±_2.38)|3.22 (_±_2.67)|
||Adpositions|2.04 (0.56)|12.29 (_±_3.52)|12.49 (_±_3.26)|12.35 (_±_2.77)|11.81 (_±_2.88)|
|POS|Adverbs|20.24 (_<_0.001)|3.41 (_±_2.31)|3.89 (_±_2.68)|4.52 (_±_2.36)|4.97 (_±_2.56)|
||Auxiliaries|10.27 (0.02)|3.98 (_±_2.63)|3.8 (_±_2.65)|4.03 (_±_2.56)|4.93 (_±_2.36)|
||Coordinating conj.|14.86 (0.002)|6.91 (_±_2.64)|5.81 (_±_3)|5.63 (_±_2.38)|5.87 (_±_2.16)|
||Determiners|25.78 (_<_0.001)|13.77 (_±_2.89)|13.88 (_±_2.57)|13.57 (_±_2.58)|12.27 (_±_2.3)|


------------------------- PAGINA 19 --------------------------

|||||**Average V**|**alues (SD)**||
|---|---|---|---|---|---|---|
|**Group**|**Feature**|**_χ_ (****_p_)**|**B**|**HP**|**U**|**PU**|
||Interjections|0.95 (0.81)|0.05 (_±_0.43)|0.02 (_±_0.19)|0.03 (_±_0.17)|0.04 (_±_0.23)|
||Lexical density|3.61 (0.31)|0.45 (_±_0.04)|0.45 (_±_0.04)|0.46 (_±_0.03)|0.45 (_±_0.03)|
||<br>Nouns<br>Numerals|31.03 (_<_0.001)<br>12.51 (0.006)|17.64 (_±_3.21)<br>2.26 (_±_1.72)|18.32 (_±_3.02)<br>1.98 (_±_1.33)|17.58 (_±_2.83)<br>1.86 (_±_1.28)|15.9 (_±_2.48)<br>1.58 (_±_0.87)|
|POS|Pronouns|<br>5.85 (0.12)|<br>7.57 (_±_2.73)|<br>7.75 (_±_3.16)|<br>6.92 (_±_3.2)|<br>8.08 (_±_2.37)|
||Proper nouns|12.96 (0.005)|1.57 (_±_1.77)|1.58 (_±_1.65)|1.33 (_±_1.3)|2.06 (_±_1.38)|
||<br>Subordinating conj.|<br>26.16 (_<_0.001)|<br>2.49 (_±_2.32)|<br>3.89 (_±_2.4)|<br>3.7 (_±_2.4)|<br>4.12 (_±_2.39)|
||Verbs|4.67 (0.2)|14.74 (_±_3.64)|14.63 (_±_3.04)|13.96 (_±_3.96)|13.97 (_±_2.88)|
||X|15.85 (0.001)|0.02 (_±_0.17)|0.03 (_±_0.22)|0.01 (_±_0.06)|0.11 (_±_0.35)|
||Aux form:fin|0.54 (0.91)|84.59 (_±_35.34)|82.58 (_±_36.7)|86.43 (_±_32.15)|95.03 (_±_13.75)|
||i<br>Aux form:ger|<br>9.43 (0.02)|<br>0 (_±_0)|<br>0.22 (_±_2.36)|<br>1.25 (_±_11.18)|<br>1 (_±_4.11)|
||<br>Aux form:inf<br>|4.43 (0.22)<br>|0.43 (_±_3.05)<br>|0.98 (_±_4.19)<br>|1.64 (_±_11.31)<br>|1.83 (_±_6.9)<br>|
||Aux form:part<br>Aux mood:cnd|7.87 (0.05)<br>6.83 (0.08)|0.39 (_±_2.38)<br>0 (_±_0)|0.15 (_±_1.57)<br>0 (_±_0)|1.93 (_±_8.43)<br>0.18 (_±_1.6)|1.01 (_±_3.93)<br>0.55 (_±_3.18)|
||Aux mood:ind|<br>1.58 (0.66)|<br>85.42 (_±_35.48)|<br>83.75 (_±_36.86)|<br>87.73 (_±_31.8)|<br>96.75 (_±_12.32)|
||Aux mood:sub|12.49 (0.006)|0 (_±_0)|0.18 (_±_1.89)|0.85 (_±_4.58)|1.56 (_±_5.89)|
||Aux num,pers:plur,1|5.93 (0.12)|7.14 (_±_21.78)|3.2 (_±_12.81)|2.39 (_±_8.29)|5.24 (_±_14.75)|
||<br>Aux num,pers:plur,3|<br>10.44 (0.02)|<br>21.69 (_±_32.24)|<br>11.93 (_±_24.77)|<br>17.16 (_±_25.05)|<br>16.83 (_±_23.92)|
||Aux num,pers:sing,1|12.3 (0.006)|1.42 (_±_5.49)|0.74 (_±_5.65)|0.42 (_±_3.73)|3.2 (_±_10.76)|
||<br>Aux num,pers:sing,3|<br>10.81 (0.01)|<br>55.16 (_±_39.77)|<br>68.06 (_±_39.71)|<br>68.78 (_±_35.06)|<br>73.15 (_±_28.39)|
||<br>Aux tense:imp|3.19 (0.36)|53.74 (_±_41.46)|60.95 (_±_42.32)|62.74 (_±_37.66)|65.79 (_±_32.84)|
||<br>Aux tense:past|<br>6.94 (0.07)|<br>21.76 (_±_34.61)|<br>11.56 (_±_24.65)|<br>18.02 (_±_26.63)|<br>13.48 (_±_21.22)|
||Aux tense:pres|17.64 (_<_0.001)|9.91 (_±_23.61)|11.41 (_±_28.24)|7.99 (_±_21.99)|19.6 (_±_30.28)|
||<br>Verb form:fin|<br>2.74 (0.43)|<br>56.57 (_±_20.34)|<br>57.09 (_±_20.77)|<br>56.09 (_±_14.56)|<br>53.25 (_±_16.51)|
||Verb form:ger|3.02 (0.39)|16.47 (_±_12.83)|18.15 (_±_13.24)|19.5 (_±_11.76)|18.29 (_±_10.02)|
|Verb<br>Inflection|<br>Verb form:inf|<br>1.01 (0.8)|<br>15.52 (_±_12.68)|<br>16.26 (_±_14.69)|<br>14.97 (_±_11.51)|<br>16.9 (_±_10.79)|
|l|Verb form:part|8.94 (0.03)|11.44 (_±_16.34)|8.51 (_±_13.36)|9.45 (_±_11.96)|11.55 (_±_12.8)|
||<br>Verb mood:cnd|<br>10.91 (0.01)|<br>2.94 (_±_9.9)|<br>2.19 (_±_10.92)|<br>5.15 (_±_11.1)|<br>3.52 (_±_9.32)|
||Verb mood:imp|4.73 (0.19)|0 (_±_0)|0.14 (_±_1.07)|0 (_±_0)|0 (_±_0)|
||<br>Verb mood:ind<br>|<br>13.95 (0.003)<br>|<br>95.61 (_±_14.08)<br>|<br>96.59 (_±_14.39)<br>|<br>93.73 (_±_11.59)<br>|<br>94.9 (_±_10.45)<br>|
||Verb mood:sub<br>Verb num,pers:plur|6.83 (0.08)<br>2.92 (0.4)|0.4 (_±_2.35)<br>0.07 (_±_0.73)|0.19 (_±_1.5)<br>0 (_±_0)|1.12 (_±_4.78)<br>0 (_±_0)|1.58 (_±_5.79)<br>0 (_±_0)|
||Verb num,pers:plur,1|5.78 (0.12)|15.13 (_±_21.8)|11.49 (_±_19.9)|16.08 (_±_19.81)|14.38 (_±_18.13)|
||<br>Verb num,pers:plur,3<br>|<br>8.09 (0.04)<br>|<br>24.47 (_±_24.18)<br>|<br>31.19 (_±_28.8)<br>|<br>21.5 (_±_23.29)<br>|<br>20.45 (_±_15.69)<br>|
||Verb num,pers:sing|4.93 (0.18)|1.61 (_±_6.74)|0.51 (_±_2.61)|0.09 (_±_0.8)|1.11 (_±_4.07)|
||<br>Verb num,pers:sing,1|<br>23.37 (_<_0.001)|<br>2.12 (_±_7.39)|<br>6.43 (_±_13.76)|<br>4.02 (_±_10.43)|<br>7.02 (_±_10.13)|
||Verb num,pers:sing,2|2.36 (0.5)|0 (_±_0)|0.07 (_±_0.73)|0 (_±_0)|0 (_±_0)|
||<br>Verb num,pers:sing,3|<br>7.32 (0.06)|<br>55.46 (_±_27.48)|<br>48.59 (_±_27.88)|<br>57.88 (_±_26.82)|<br>56.89 (_±_16.98)|
||Verb tense:fut|4.67 (0.2)|0 (_±_0)|0.87 (_±_4.64)|0.32 (_±_2.11)|0.36 (_±_1.75)|
||Vb ti|<br>719 (007)|<br>2655 (_±_2142)|<br>2449 (_±_2507)|<br>305 (_±_1876)|<br>2739 (_±_1612)|
||er ense:mp<br>Verb tense:past|. .<br>14.75 (0.002)|..<br>63.29 (_±_23.89)|..<br>53.46 (_±_32.66)|..<br>55.88 (_±_21.67)|..<br>48.31 (_±_24.72)|
||<br>Verb tense:pres|<br>22.24 (_<_0.001)|<br>10.15 (_±_16.81)|<br>21.19 (_±_30.08)|<br>13.3 (_±_19.71)|<br>23.94 (_±_24.93)|
||Verb edges (avg)|4.58 (0.21)|3.86 (_±_6.94)|2.43 (_±_5.61)|3.5 (_±_6.14)|2.39 (_±_3.86)|
||<br>Verb edges (0)|<br>3.33 (0.34)|<br>14.54 (_±_13.49)|<br>12.62 (_±_12.31)|<br>14.42 (_±_10.74)|<br>14.91 (_±_10.04)|
||<br>Verb edges (1)|<br>2.46 (0.48)|<br>27.56 (_±_16.35)|<br>27.79 (_±_15.94)|<br>29.27 (_±_16.02)|<br>30.6 (_±_12.44)|
|Verb|Verb edges (2)<br>Verb edges (3)|2.67 (0.45)<br>0.37 (0.95)|31.55 (_±_18.06)<br>17.38 (_±_13.65)|32.06 (_±_16.85)<br>18.02 (_±_15.46)|29.83 (_±_16.43)<br>16.76 (_±_15.56)|29.05 (_±_13.26)<br>16.76 (_±_10.41)|
|Predicate|Verb edges (4)|3.81 (0.28)|4.28 (_±_7.57)|5.96 (_±_9.73)|4.54 (_±_6.95)|4.99 (_±_6.08)|
||<br>Verb edges (5)|<br>4.23 (0.24)|<br>0.83 (_±_2.74)|<br>1.12 (_±_3.15)|<br>1.67 (_±_3.7)|<br>1.31 (_±_3.16)|
||Verb edges (6)|7.79 (0.05)|2.6 (_±_0.43)|2.72 (_±_0.42)|2.61 (_±_0.38)|2.62 (_±_0.33)|
||<br>Verbal heads per sent|<br>9.65 (0.02)|<br>2.77 (_±_1)|<br>3.07 (_±_1.16)|<br>3.14 (_±_1.16)|<br>3.14 (_±_0.96)|
||Verbal root (%)|8.6 (0.04)|90.65 (_±_18.66)|94.54 (_±_12.67)|91.45 (_±_13.91)|90.57 (_±_13.74)|
||Link length (avg)|16.34 (_<_0.001)|7.96 (_±_3.34)|9.14 (_±_4.17)|9.83 (_±_4.57)|9.63 (_±_3.37)|
||<br>Tree depth (avg max)|<br>10.15 (0.02)|<br>2.4 (_±_0.35)|<br>2.44 (_±_0.35)|<br>2.55 (_±_0.42)|<br>2.54 (_±_0.37)|
||<br>Link lenth (av max)|<br>2552 (_<_0001)|<br>1177 (_±_522)|<br>1308 (_±_684)|<br>159 (_±_871)|<br>1689 (_±_803)|
||g g<br>Prep. chain length (avg)|..<br>34.42 (_<_0.001)|..<br>1.74 (_±_1.83)|..<br>1.62 (_±_1.26)|..<br>2.64 (_±_2.59)|..<br>3.35 (_±_2.59)|
|Tree|<br>Tokens er clause (av)|<br>694 (007)|<br>083 (_±_048)|<br>092 (_±_049)|<br>093 (_±_044)|<br>098 (_±_042)|
|Structure|p  g<br>Link length (max)|. .<br>1.15 (0.77)|..<br>71.1 (_±_41.88)|..<br>73.75 (_±_42.15)|..<br>76.22 (_±_36.74)|..<br>78.62 (_±_34.43)|
||<br>n. prepositional chains<br>|2.51 (0.47)<br>|5.98 (_±_15.68)<br>|9.14 (_±_25.85)<br>|6.24 (_±_14.26)<br>|7.4 (_±_16.26)<br>|
||Prepositional distr. (1)|14.6 (0.002)|0 (_±_0)|0.15 (_±_1.57)|1.29 (_±_5.55)|1.49 (_±_4.86)|
||<br>Prepositional distr(2)|154 (067)|68 (_±_155)|677 (_±_146)|72 (_±_212)|68 (_±_126)|
||. <br>Prepositional distr. (3)|. .<br>15.37 (0.002)|..<br>4.05 (_±_1.05)|..<br>4.46 (_±_1.44)|..<br>4.55 (_±_1.11)|..<br>4.49 (_±_1.03)|


------------------------- PAGINA 20 --------------------------

|||||**Average V**|**alues (SD)**||
|---|---|---|---|---|---|---|
|**Group**|**Feature**|**_χ_ (****_p_)**|**B**|**HP**|**U**|**PU**|
||Object post-verbal|5.47 (0.14)|66.32 (_±_18.4)|66.03 (_±_18.89)|71.33 (_±_20.4)|64.69 (_±_16)|
||Object pre-verbal|5.47 (0.14)|33.68 (_±_18.4)|33.97 (_±_18.89)|28.67 (_±_20.4)|35.31 (_±_16)|
|Order|<br>Subject post-verbal|<br>20.82 (_<_0.001)|<br>6.23 (_±_16.52)|<br>10.23 (_±_20.21)|<br>16.88 (_±_26.63)|<br>15.98 (_±_22.28)|
||Subject pre-verbal|11.34 (0.01)|85.44 (_±_30.66)|86.2 (_±_26.12)|76.87 (_±_32.99)|82.88 (_±_23.95)|
||Adnominal clauses|18.33 (_<_0.001)|2 (_±_1.93)|1.97 (_±_2.25)|2.94 (_±_1.93)|2.25 (_±_1.88)|
||Relative clauses|15.77 (0.001)|0.19 (_±_0.63)|0.23 (_±_0.7)|0.31 (_±_0.71)|0.37 (_±_0.64)|
||Adverbial clauses|0.86 (0.83)|2.91 (_±_2.36)|3.02 (_±_2.17)|2.87 (_±_2.03)|3.03 (_±_1.7)|
||Adverbial modifiers|<br>16.63 (_<_0.001)|<br>3.05 (_±_2.14)|<br>3.35 (_±_2.53)|<br>3.98 (_±_2.11)|<br>4.27 (_±_2.19)|
||i<br>Adjectival modifiers|4.73 (0.19)|0.69 (_±_1.19)|0.75 (_±_1.1)|0.58 (_±_0.9)|0.85 (_±_1.1)|
||Appositions|3.7 (0.3)|2.91 (_±_2.49)|2.92 (_±_2.31)|2.73 (_±_2.23)|3.31 (_±_2.13)|
||Auxiliaries|9.5 (0.02)|0.18 (_±_0.58)|0.07 (_±_0.35)|0.2 (_±_0.56)|0.19 (_±_0.47)|
||Auxiliary passes|<br>1.42 (0.7)|<br>11.38 (_±_3.53)|<br>11.21 (_±_3.37)|<br>11.5 (_±_2.75)|<br>10.86 (_±_2.75)|
||<br>Case markers|4.66 (0.2)|0.38 (_±_0.86)|0.53 (_±_1.01)|0.44 (_±_0.78)|0.51 (_±_0.73)|
||Coordinating conj.|15.24 (0.002)|0.05 (_±_0.31)|0.03 (_±_0.24)|0.1 (_±_0.38)|0.14 (_±_0.39)|
||<br>Clausal complements|17.32 (_<_0.001)|5.69 (_±_2.84)|4.2 (_±_3.13)|4.67 (_±_2.7)|4.7 (_±_2.29)|
||Conjunctions|12.16 (0.007)|6.76 (_±_2.69)|5.72 (_±_2.97)|5.57 (_±_2.35)|5.84 (_±_2.18)|
||Copula|<br>19.33 (_<_0.001)|<br>0.75 (_±_1.28)|<br>0.79 (_±_1.25)|<br>1.02 (_±_1.2)|<br>1.31 (_±_1.23)|
|Syntactic|Clausal subjects|23.18 (_<_0.001)|13.63 (_±_2.97)|13.97 (_±_2.58)|13.52 (_±_2.48)|12.34 (_±_2.32)|
|Dep|<br>Determiners|<br>20.49 (_<_0.001)|<br>6.97 (_±_2.73)|<br>7.43 (_±_2.58)|<br>6.41 (_±_2.39)|<br>5.94 (_±_1.99)|
||Fixed mwe|2.12 (0.55)|0.74 (_±_1.17)|0.95 (_±_1.3)|0.88 (_±_1.16)|0.76 (_±_0.99)|
||Flat mwe|9.87 (0.02)|0 (_±_0)|0 (_±_0)|0 (_±_0)|0.03 (_±_0.15)|
||Indirect objects|12.95 (0.005)|3.99 (_±_2.47)|3.97 (_±_2.66)|2.88 (_±_2.16)|3.24 (_±_1.78)|
||<br>Markers|<br>23.79 (_<_0.001)|<br>3.33 (_±_2.42)|<br>4.84 (_±_2.64)|<br>4.4 (_±_2.82)|<br>4.88 (_±_2.49)|
||Nominal modifiers|4.52 (0.21)|3.12 (_±_2.54)|3.06 (_±_2.07)|3.37 (_±_2.3)|3.64 (_±_2.23)|
||Nominal subjects|4.65 (0.2)|4.3 (_±_2.44)|4.52 (_±_2.39)|3.88 (_±_2.39)|3.9 (_±_1.79)|
||<br>Nominal subject passes|<br>4.06 (0.26)|<br>0.06 (_±_0.35)|<br>0.01 (_±_0.08)|<br>0.07 (_±_0.35)|<br>0.06 (_±_0.23)|
||<br>Numeral modifiers|<br>11.79 (0.008)|<br>2.06 (_±_1.67)|<br>1.94 (_±_1.36)|<br>1.69 (_±_1.25)|<br>1.44 (_±_0.89)|
||i<br>Direct objects|3.51 (0.32)|5.48 (_±_2.63)|5.77 (_±_3.05)|6.07 (_±_2.52)|5.71 (_±_2.05)|
||Oblique complements|4.83 (0.18)|1.03 (_±_1.33)|0.88 (_±_1.22)|1.15 (_±_1.42)|1.14 (_±_1.21)|
||Parataxis|18.52 (_<_0.001)|0.56 (_±_1.01)|0.52 (_±_0.89)|0.61 (_±_0.95)|0.98 (_±_1.02)|
||Roots|<br>11.11 (0.01)|<br>1.54 (_±_1.67)|<br>2.39 (_±_2)|<br>2.28 (_±_2.27)|<br>2.09 (_±_1.77)|
||Open clausal compl.|<br>17.55 (_<_0.001)|<br>6 (_±_1.67)|<br>5.53 (_±_1.73)|<br>5.14 (_±_1.51)|<br>5.13 (_±_1.24)|
||principal prop. distr.|16.8 (_<_0.001)|48.88 (_±_17.55)|44.64 (_±_17.79)|42 (_±_17.46)|40.8 (_±_12.83)|
||subord. chain len. (avg)|17.68 (_<_0.001)|1.13 (_±_0.31)|1.17 (_±_0.32)|1.2 (_±_0.4)|1.25 (_±_0.22)|
||subordinate distr. (1)|12.31 (0.006)|84.01 (_±_26.52)|80.23 (_±_25.64)|76 (_±_28.2)|79.33 (_±_15.84)|
||subordinate distr. (2)|10.6 (0.01)|12.66 (_±_22.5)|15.13 (_±_20.88)|16.53 (_±_21.99)|16.73 (_±_14.01)|
|Subord|subordinate distr. (3)|<br>10.32 (0.02)|<br>0.99 (_±_4.79)|<br>1.66 (_±_6.66)|<br>3.72 (_±_14.31)|<br>3.75 (_±_9.13)|
||subordinate distr. (4)|<br>1.88 (0.6)|<br>0.26 (_±_2.55)|<br>0.3 (_±_2.22)|<br>0 (_±_0)|<br>0.2 (_±_1.31)|
||subordinate post|2.04 (0.56)|88.53 (_±_25.78)|90.53 (_±_23.23)|90.12 (_±_23.36)|92.33 (_±_13.04)|
||<br>subordinate pre|4.57 (0.21)|9.39 (_±_22.32)|6.79 (_±_17.7)|6.13 (_±_15.05)|7.67 (_±_13.04)|
||<br>subordinate prop. distr.|16.8 (_<_0.001)|51.12 (_±_17.55)|55.36 (_±_17.79)|58 (_±_17.46)|59.2 (_±_12.83)|

# **References**

1. Smith, H.M.J.; Ryder, H.; Flowe, H.D. Eyewitness evidence. In _Forensic Psychology: Crime, Justice, Law, Interventions_ ; Wiley: Hoboken, NJ, USA, 2017; pp. 173–192.

2. Baddeley, A. Qué es la memoria. In _Memória_ , 2nd ed.; Alianza Editorial: Madrid, Spain, 2018; pp. 25–43.

3. Mazzoni, G. _Psicología del Testimonio_ ; Trotta: Roma, Italy, 2019; pp. 11–23.

4. Ayala, R. Witness testimonial credibility in criminal proceedings. _Rev. Bras. Direito Process. Penal_ **2020** , _6_ , 453–480.

5. Manzanero, A. _Memoria de Testigos: Obtención y Valoración de la Prueba Testifical_ ; Pirámide: Madrid, Spain, 2010; pp. 23–62.

6. Smith-Spark, J.H.; Bartimus, J.; Wilcock, R. Mental time travel ability and the Mental Reinstatement of Context for crime witnesses. _Conscious. Cogn._ **2017** , _48_ , 1–10. [CrossRef]

7. Glomb, K. How to improve eyewitness testimony research: Theoretical and methodological concerns about experiments on the impact of emotions on memory performance. _Psychol. Res._ **2022** , _86_ , 1–11. [CrossRef]

8. Marr, C.; Otgaar, H.; Sauerland, M.; Quaedflieg, C.; Hope, L. The effects of stress on eyewitness memory: A survey of memory experts and laypeople. _Mem. Cogn._ **2021** , _49_ , 401–421. [CrossRef] [PubMed]

9. Flowe, H.D.; Colloff, M.F.; Kloft, L.; Jores, T.; Stevens, L.M. Impact of alcohol and other drugs on eyewitness memory. In _The Routledge International Handbook of Legal and Investigative Psychology_ ; Taylor and Francis: Abingdon, UK, 2019; pp. 149–162.


------------------------- PAGINA 21 --------------------------

10. Murphy, G.; Loftus, E.; Grady, R.; Levine, L.; Greene, C. False memories for fake news during Ireland’s abortion referendum. _Psychol. Sci._ **2019** , _30_ , 1449–1459. [CrossRef]

11. Manzanero, A.L. Memoria de testigos. In _La Memoria Humana: Aportaciones Desde la Neurociencia Cognitiva_ ; Ediciones Pirámide: Madrid, Spain, 2015; pp. 310–336.

12. Mugno, A.P.; Malloy, L.C.; La Rooy, D. Interviewing Witnesses. In _Forensic Psychology: Crime, Justice, Law, Interventions_ ; John Wiley & Sons: Hoboken, NJ, USA, 2017; pp. 201–223.

13. Tulving, E.; Thomson, D.M. Encoding specificity and retrieval processes in episodic memory. _Psychol. Rev._ **1973** , _80_ , 352. [CrossRef]

14. Milne, R.; Bull, R. Back to basics: A componential analysis of the original cognitive interview mnemonics with three age groups. _Appl. Cogn. Psychol._ **2002** , _16_ , 743–753. [CrossRef]

15. Memon, A.; Meissner, C. The Cognitive Interview: A Meta-Analytic Review and Study Space Analysis of the Past 25 Years. _Psychol. Public Policy Law_ **2010** , _16_ , 340–372. [CrossRef]

16. Demir, M. The perceived effect of a witness security program on willingness to testify. _Int. Crim. Justice Rev._ **2018** , _28_ , 62–81. [CrossRef]

17. Coxon, P.; Valentine, T. The effects of the age of eyewitnesses on the accuracy and suggestibility of their testimony. _Appl. Cogn. Psychol. Off. J. Soc. Appl. Res. Mem. Cogn._ **1997** , _11_ , 415–430. [CrossRef]

18. Areh, I. Gender-related differences in eyewitness testimony. _Personal. Individ. Differ._ **2011** , _50_ , 559–563. [CrossRef]

19. Pilar, D.R.; Jaeger, A.; Gomes, C.F.; Stein, L.M. Passwords usage and human memory limitations: A survey across age and educational background. _PLoS ONE_ **2012** , _7_ , e51067. [CrossRef] [PubMed]

20. Loftus, E.F.; Levidow, B.; Duensing, S. Who remembers best? Individual differences in memory for events that occurred in a science museum. _Appl. Cogn. Psychol._ **1992** , _6_ , 93–107. [CrossRef]

21. Stern, Y. What is cognitive reserve? Theory and research application of the reserve concept. _J. Int. Neuropsychol. Soc._ **2002** , _8_ , 448–460. [CrossRef] [PubMed]

22. Ostrosky-Solís, F.; Esther Gómez-Pérez, M.; Matute, E.; Rosselli, M.; Ardila, A.; Pineda, D. Neuropsi attention and memory: A neuropsychological test battery in Spanish with norms by age and educational level. _Appl. Neuropsychol._ **2007** , _14_ , 156–170. [CrossRef] [PubMed]

23. Frick, A.; Wright, H.; Fay, S.; Vanneste, S.; Angel, L.; Bouazzaoui, B.; Taconnat, L. The protective efect of educational level varies as a function of the difculty of the memory task in ageing. _J. Int. Neuropsychol. Soc._ **2022** , _19_ , 1407–1415.

24. Bangs, K.; Smith-Spark, J. Mental Reinstatement of Context: Do individual differences in mental time travel and eyewitness occupation influence eyewitness performance over different delay intervals? _J. Investig. Psychol. Offender Profiling_ **2019** , _17_ , 31–45. [CrossRef]

25. Faber, P.; Nielsen, N.P.; Berntsen, D. Effects of mental context reinstatement on accuracy and recollective experience. _Appl. Cogn. Psychol._ **2023** , _37_ , 1004–1015. [CrossRef]

26. Steller, M.; Köhnken, G. Criteria-Based Content Analysis. In _Psychological Methods in Criminal Investigation and Evidence_ ; Raskin, D.C., Ed.; Springer: New York, NY, USA, 1989; pp. 217–245.

27. Volbert, R.; Steller, M. Is this testimony truthful, fabricated, or based on false memory? Credibility assessment 25 years after S teller and Köhnken (1989). _Eur. Psychol._ **2014** , _19_ , 207–220. [CrossRef]

28. Juola, P. Detecting stylistic deception. In Proceedings of the Workshop on Computational Approaches to Deception Detection, Avignon, France, 23–27 April 2012; pp. 91–96.

29. Galasinski, D. _The Language of Deception: A Discourse Analytical Study_ ; Sage Publications: Thousand Oaks, CA, USA, 2000.

30. Jakupov, A.; Longhi, J.; Zeddini, B. The Language of Deception: Applying Findings on Opinion Spam to Legal and Forensic Discourses. _Languages_ **2023** , _9_ , 10. [CrossRef]

31. Newman, M.L.; Pennebaker, J.W.; Berry, D.S.; Richards, J.M. Lying words: Predicting deception from linguistic styles. _Personal. Soc. Psychol. Bull._ **2003** , _29_ , 665–675. [CrossRef] [PubMed]

32. Ott, M.; Cardie, C.; Hancock, J.T. Negative deceptive opinion spam. In Proceedings of the 2013 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Atlanta, GA, USA, 9–14 June 2013; pp. 497–501.

33. Potthast, M.; Kiesel, J.; Reinartz, K.; Bevendorff, J.; Stein, B. A Stylometric Inquiry into Hyperpartisan and Fake News. In Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers), Melbourne, Australia, 15–20 July 2018; Gurevych, I., Miyao, Y., Eds.; 2018; pp. 231–240. [CrossRef]

34. Van Der Zee, S.; Poppe, R.; Havrileck, A.; Baillon, A. A personal model of trumpery: Linguistic deception detection in a real-world high-stakes setting. _Psychol. Sci._ **2022** , _33_ , 3–17. [CrossRef] [PubMed]

35. Fornaciari, T.; Poesio, M. Automatic deception detection in Italian court cases. _Artif. Intell. Law_ **2013** , _21_ , 303–340. [CrossRef]

36. Pennebaker, J.W.; Francis, M.E.; Booth, R.J. Linguistic inquiry and word count: LIWC 2001. _Mahway Lawrence Erlbaum Assoc._ **2001** , _71_ , 2001.


------------------------- PAGINA 22 --------------------------

37. Vrij, A.; Mann, S.; Kristen, S.; Fisher, R.P. Cues to deception and ability to detect lies as a function of police interview styles. _Law Hum. Behav._ **2007** , _31_ , 499–518. [CrossRef] [PubMed]

38. Hazra, S.; Majumder, B.P. To Tell The Truth: Language of Deception and Language Models. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), Mexico City, Mexico, 16–21 June 2024; pp. 8498–8512.

39. Tucker, T.A. Implicit Bias and the Corresponding Effects on False Memories. Ph.D Thesis, Middle Tennessee State University, Murfreesboro, TN, USA, 2019.

40. Helm, R.K.; Ceci, S.J.; Burd, K.A. Can implicit associations distinguish true and false eyewitness memory? Development and preliminary testing of the IATe. _Behav. Sci. Law_ **2016** , _34_ , 803–819. [CrossRef] [PubMed]

41. Solà-Sales, S.; Alzetta, C.; Moret-Tatay, C.; Dell’Orletta, F. Analysing Deception in Witness Memory through Linguistic Styles in Spontaneous Language. _Brain Sci._ **2023** , _13_ , 317. [CrossRef]

42. Powers, W.R. _Transcription Techniques for the Spoken Word_ ; Rowman Altamira: Lanham, MD, USA, 2005.

43. Vogler, N.; Pearl, L. Using linguistically defined specific details to detect deception across domains. _Nat. Lang. Eng._ **2019** , _26_ , 349–373. [CrossRef]

44. Feng, S.; Banerjee, R.; Choi, Y. Syntactic stylometry for deception detection. In Proceedings of the 50th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers), Jeju Island, Republic of Korea, 8–14 July 2012; pp. 171–175.

45. Mihalcea, R.; Strapparava, C. The lie detector: Explorations in the automatic recognition of deceptive language. In Proceedings of the ACL-IJCNLP 2009 Conference Short Papers, Suntec, Singapore, 4 August 2009; pp. 309–312.

46. Pérez-Rosas, V.; Abouelenien, M.; Mihalcea, R.; Burzo, M. Deception detection using real-life trial data. In Proceedings of the 2015 ACM on International Conference on Multimodal Interaction, Seattle, WA, USA, 9–13 November 2015, pp. 59–66.

47. Quijano-Sánchez, L.; Liberatore, F.; Camacho-Collados, J.; Camacho-Collados, M. Applying automatic text-based detection of deceptive language to police reports: Extracting behavioral patterns from a multi-step classification model to understand how we lie to the police. _Knowl. Based Syst._ **2018** , _149_ , 155–168. [CrossRef]

48. Almela, Á. A Corpus-Based Study of Linguistic Deception in Spanish. _Appl. Sci._ **2021** , _11_ , 8817. [CrossRef]

49. Brunato, D.; Cimino, A.; Dell’Orletta, F.; Venturi, G.; Montemagni, S. Profiling-UD: A Tool for Linguistic Profiling of Texts. In Proceedings of the Proceedings of The 12th Language Resources and Evaluation Conference, Marseille, France, 11–16 May 2020; pp. 7147–7153.

50. Straka, M.; Hajic, J.; Straková, J. UDPipe: Trainable pipeline for processing CoNLL-U files performing tokenization, morphological analysis, pos tagging and parsing. In Proceedings of the Tenth International Conference on Language Resources and Evaluation (LREC’16), Portoroz, Slovenia, 23–28 May 2016; pp. 4290–4297.

51. Deutsch, T.; Jasbi, M.; Shieber, S. Linguistic Features for Readability Assessment. In Proceedings of the Fifteenth Workshop on Innovative Use of NLP for Building Educational Applications, Seattle, WA, USA, 10 July 2020; Burstein, J., Kochmar, E.; Leacock, C.; Madnani, N.; Pilán, I.; Yannakoudakis, H.; Zesch, T., Eds.; 2020; pp. 1–17. [CrossRef]

52. van Halteren, H. The Detection of Inconsistency in Manually Tagged Text. In Proceedings of the COLING—2000 Workshop on Linguistically Interpreted Corpora, Centre Universitaire, Luxembourg, 6 August 2000; Abeille, A., Brants, T., Uszkoreit, H., Eds.; 2000; pp. 48–55.

53. Maier, B.; Niehaus, S.; Wacholz, S.; Volbert, R. The Strategic Meaning of CBCA Criteria From the Perspective of Deceivers. _Front. Psychol._ **2018** , _9_ , 855. [CrossRef] [PubMed]

54. Theunissen, T.; Meyer, T.; Memon, A.; Weinsheimer, C. Adult Eyewitness Memory for Single Versus Repeated Traumatic Events. _Appl. Cogn. Psychol._ **2017** , _31_ , 164–174. [CrossRef]

55. Van Oorsouw, K.; Broers, N.; Sauerland, M. Alcohol intoxication impairs eyewitness memory and increases suggestibility: Two field studies. _Appl. Cogn. Psychol._ **2019** , _33_ , 439–455. [CrossRef]

56. Wechsler, H.J.; Kehn, A.; Wise, R.A.; Cramer, R.J. Attorney beliefs concerning scientific evidence and expert witness credibility. _Int. J. Law Psychiatry_ **2015** , _41_ , 58–66. [CrossRef]

57. Ghetti, S.; Bunge, S.A. Neural changes underlying the development of episodic memory during middle childhood. _Dev. Cogn. Neurosci._ **2012** , _2_ , 381–395. [CrossRef]

58. Geiselman, R.; Fisher, R.; MacKinnon, D.; Holland, H. Enhancement of Eyewitness Memory with the Cognitive Interview. _Am. J. Psychol._ **1986** , _99_ , 385–401. [CrossRef]

59. Wilcock, R.A.; Bull, R.; Vrij, A. Are old witnesses always poorer witnesses? Identification accuracy, context reinstatement, own-age bias. _Psychol. Crime Law_ **2007** , _13_ , 305–316. [CrossRef]

60. Bosch, S.; Jehee, J.; Fernández, G.; Doeller, C. Reinstatement of Associative Memories in Early Visual Cortex Is Signaled by the Hippocampus. _J. Neurosci._ **2014** , _34_ , 7493–7500. [CrossRef]

61. Wing, E.; Maureen, R.; Cabeza, R. Reinstatement of individual past events revealed by the similarity of distributed activation patterns during encoding and retrieval. _J. Cogn. Neurosci._ **2015** , _27_ , 679–691. [CrossRef] [PubMed]

62. Wixted, J.T. Time to exonerate eyewitness memory. _Forensic Sci. Int._ **2018** , _292_ , e13–e15. [CrossRef] [PubMed]


------------------------- PAGINA 23 --------------------------

63. Gudjonsson, G.; Clare, I. The relationship between confabulation and intellectual ability, memory, interrogative suggestibility and acquiescence. _Personal. Individ. Differ._ **1995** , _19_ , 333–338. [CrossRef]

64. McCornack, S.; Morrison, K.; Paik, J.; Wisner, A.; Zhu, X. Information Manipulation Theory 2: A Propositional Theory of Deceptive Discourse Production. _J. Lang. Soc. Psychol._ **2014** , _33_ , 348–377. [CrossRef]

65. Lanciano, T.; Curci, A. Memory for emotional events: The accuracy of central and peripheral details. _Eur. J. Psychol._ **2011** , _7_ , 323–336. [CrossRef]

66. Gubi-Kelm, S.; Schmidt, A. Interrogator intonation and memory encoding performance. _PLoS ONE_ **2019** , _14_ , e0218331. [CrossRef] [PubMed]

67. Guerrero-Sastoque, L.; Bouazzaoui, B.; Burger, L.; Taconnat, L. Effet du niveau d’études sur les performances en mémoire épisodique chez des adultes âgés: Rôle médiateur de la métamémoire. _Psychol. Française_ **2021** , _66_ , 111–126. [CrossRef]

68. Stern, Y. How Can Cognitive Reserve Promote Cognitive and Neurobehavioral Health? _Arch. Clin. Neuropsychol._ **2021** , _36_ , 1291–1295. [CrossRef]

69. Lövdén, M.; Fratiglion, L.; Glymour, M.; Lindenberger, U.; Tucker-Drob, E. Education and cognitive functioning across the life span. _Psychol. Sci. Public Int. J. Am. Psychol. Soc._ **2020** , _21_ , 6–41. [CrossRef] [PubMed]

**Disclaimer/Publisher’s Note:** The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.


------------------------- PAGINA 24 --------------------------

Copyright of Information (2078-2489) is the property of MDPI and its content may not be copied or emailed to multiple sites or posted to a listserv without the copyright holder's express written permission. However, users may print, download, or email articles for individual use.
