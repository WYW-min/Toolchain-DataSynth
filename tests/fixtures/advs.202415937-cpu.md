RESEARCH ARTICLE

www.advancedscience.com

Engineering Multi-Site Platinum Ensembles Synergistically
Boosts Catalysis

Tao Dong, Fei Xiao, Xuanning Wu, Tao Ban, Jian Ji, Biyuan Liu, Jiarui Zhang, Jiuxing Jiang,
Dieqing Zhang, Weixing Yang, Gaoyuan Liu, Xin Yang, and Haibao Huang*

Engineering stable and eﬃcient noble metal ensembles with multi-type active
sites while understanding the role of each site at the atomic level remains
a signiﬁcant challenge in heterogeneous catalysis. Herein, a sub-nanometric
Pt ensemble catalyst with a diverse array of active sites is constructed via a
dual-conﬁnement strategy, which exhibits superior activity and durability with
minimal Pt loading (0.13 wt.%). Simultaneously, the roles of diﬀerent Pt sites at
the atomic scale are determined through in situ characterization methods and
density functional theory (DFT) calculations. Speciﬁcally, Pt top sites predom-
inantly serve as pivotal centers for O═O bond activation, whereas Pt−O−Si
interfacial sites primarily govern the activation of H─OH and C─H bonds.
2−, and −OH) generated from O2 and
The reactive oxygen species (O2
H2O activation synergistically enhance formaldehyde (HCHO) oxidation and
shorten the reaction pathway. This study sheds light on a better understanding
and rational design of catalyst active sites via precise synthesis of multi-site
ensembles or discerning the distinct contributions of various catalytic sites.

−, O2

1. Introduction

Synergistic collaboration among researchers and institutions
in large-scale scientiﬁc projects, such as the Human Genome
Project (HGP) and the development of the Large Hadron Col-
lider (LHC), demonstrates the critical role of synergistic interac-
tions in driving signiﬁcant progress and success in human soci-
ety. Similarly, in the microscopic particle world of heterogeneous
catalysis, the synergistic interactions among catalytic sites, which

aim to reduce costs and enhance eﬃciency,
are also crucial. Particularly in complex cat-
alytic reactions, chemical bond cleavage,
and formation are frequently dominated by
speciﬁc metal active sites, which require
synergistic interactions between distinct
catalytic sites to obtain high catalytic activ-
ity and selectivity.[1,2] This synergistic inter-
action among catalytic sites, known as the
“ensemble eﬀect” was described by Sachtler
et al. in the 1970s.[3] For example, formalde-
hyde (HCHO), a highly toxic indoor pol-
lutant, has garnered signiﬁcant attention
from the International Agency for Research
on Cancer (IRAC) due to its potential to
cause severe health hazards, highlighting
the urgent need for eﬀective removal.[4,5]
Catalytic oxidation of HCHO is a common
yet crucial area involving the cleavage of
various chemical bonds, including O═O,
H─OH, and C─H bonds.[6] It is evident
that a single type of active site is generally
insuﬃcient for the simultaneous activation of all bonds due to
competitive adsorption among the reactant molecules.[7] Conse-
quently, designing catalysts with multiple functional ensemble
sites is signiﬁcantly important for maintaining high catalytic per-
formance in complex reactions.

In recent years, a substantial amount of research has been de-
voted to the design of catalyst active sites, such as single atoms
and nanoclusters.[8–10] This is particularly for supported noble

T. Dong, F. Xiao, X. Wu, B. Liu, J. Zhang, X. Yang, H. Huang
School of Environmental Science and Engineering
Sun Yat-sen University
Guangzhou 510006, China
E-mail: huanghb6@sysu.edu.cn
T. Ban, H. Huang
College of Ecology and Environment
School of Chemical Engineering and Technology
Xinjiang University
Urumqi 830017, China

The ORCID identiﬁcation number(s) for the author(s) of this article
can be found under https://doi.org/10.1002/advs.202415937

© 2025 The Author(s). Advanced Science published by Wiley-VCH
GmbH. This is an open access article under the terms of the Creative
Commons Attribution License, which permits use, distribution and
reproduction in any medium, provided the original work is properly cited.

DOI: 10.1002/advs.202415937

J. Ji
School of Resources and Environment
Nanchang University
Nanchang 330031, China
J. Jiang
MOE Key Laboratory of Bioinorganic and Synthetic Chemistry
School of Chemistry
Sun Yat-sen University
Guangzhou 510006, China
D. Zhang
The Education Ministry Key Lab of Resource Chemistry
College of Chemistry and Materials Science
Shanghai Normal University
Shanghai 200234, China
W. Yang, G. Liu
Midea Group
Foshan 528300, China

Adv. Sci. 2025, 12, 2415937

2415937 (1 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

metal catalysts, emerging as a pivotal research focus in the areas
of hydrogen production,[11] carbon monoxide (CO) oxidation,[12]
organic synthesis,[13] and volatile organic compounds (VOCs)
degradation.[14] For instance, Xie et al.[15] prepared a Pd-Cu dual
sites cluster catalyst that exhibits excellent C2+ selectivity in CO2
reduction reaction. Zhang et al.[1] prepared a supported Rh cat-
alyst with both isolated atoms and ensemble sites that exhibits
excellent catalytic eﬃciency in the conversion of cyclohexanol
to phenol. However, a signiﬁcant challenge remains in design-
ing noble metal ensembles at the atomic scale to expose multi-
type active sites while ensuring their stability. Currently, mod-
ulating the interactions between noble metals and support to
achieve the construction and stability of active sites is the most
frequently studied and eﬀective strategy.[16–18] Typically, local in-
teractions between noble metal and support materials are estab-
lished through a high-temperature reduction or oxidation treat-
ment to stabilize active sites.[19,20] Nevertheless, when noble met-
als are dispersed at the scale of single atoms and nanoclusters,
they often exhibit poor temperature resistance due to the in-
creased surface free energy.[21] This makes single atoms or nan-
oclusters readily agglomerate into large particles even in the ex-
istence of strong metal-support interactions or even at room
temperature, resulting in a decrease in active sites and subse-
quent catalyst deactivation.[22,23] Therefore, maintaining abun-
dant types and quantities of active sites to achieve an ensemble
eﬀect is key for the long-term eﬃcient operation of catalysts.

Based on this, researchers are committed to developing more
eﬀective methods to stabilize and disperse noble metal ensem-
bles onto speciﬁc anchoring sites of the support materials. So
far, 3D ﬂaky cross-linked structured oxides or hierarchical porous
materials (e.g., TiO2, Al2O3, SiO2, zeolite) have emerged as
promising candidates for stabilizing noble metal active sites due
to their unique geometric structures, physical characteristics, and
tunable surface sites.[24,25] In particular, the 3D nanoﬂower meso-
porous SiO2 (NFM-SiO2) has attracted extensive attention due to
its abundant mesoporous structure and surface hydroxyl groups
(─OH), unique sheet cross-linked structure, and high thermal
stability.[26] The lamellar surfaces are rich in anchoring sites—
surface hydroxyl groups—that can robustly bind to noble metals
and form new types of active sites, such as metal-support interfa-
cial sites (e.g., metal–O–Si or metal–Si sites).[6,27,28] In addition,
the spatial conﬁnement provided by the SiO2 layers acts as an ef-
fective barrier, substantially blocking the migration of noble met-
als and maintaining the abundance of active sites.[26] From this
perspective, NFM-SiO2 would exhibit outstanding advantages in
the construction of multi-type noble metal active sites while si-
multaneously maintaining the stability of the noble metal ensem-
bles.

In this study, we precisely designed and synthesized a sub-
nanometric Pt ensemble catalyst with multi-type active sites sta-
ble on a 3D NFM-SiO2 surface (named Pt@NFM-SiO2-400) via
an interface and surface space dual-conﬁnement strategy. The
Pt@NFM-SiO2-400 exhibited excellent catalytic activity and dura-
bility of HCHO oxidation with minimal Pt loading (0.13 wt.%),
which can be attributed to the synergistic interactions among
the various active sites. Aberration-corrected scanning transmis-
sion electron microscopy (AC-STEM) revealed that the structural
conﬁguration and aggregation morphology of Pt ensembles un-
dergo dynamic migration and redistribution at varying reduction

temperatures. Surprisingly, uniformly dispersed sub-nanometric
Pt clusters were exclusively obtained at a reduction tempera-
ture of 400 °C. Furthermore, the extended X-ray absorption ﬁne
structure (EXAFS), CO-adsorption diﬀuse reﬂectance infrared
Fourier transform spectroscopy (CO-DRIFTS), and DFT calcu-
lations conﬁrmed the Pt ensembles with multi-type active sites,
such as Pt top sites, Pt side sites, and Pt−O−Si interfacial sites.
Speciﬁcally, the Pt top sites are the activation site of O2, while
the Pt−O−Si interfacial sites serve as the primary activation for
HCHO and H2O. Mechanistic studies demonstrated that the ac-
2−, and ─OH, generated from the activation of
tive species O2
O2 and H2O, synergistically promote the eﬀective catalytic oxida-
tion of HCHO, achieving 100% degradation at room temperature
and shortening the reaction pathway. This work inspires innova-
tive approaches for the rational design of eﬃcient heterogeneous
catalysts.

−, O2

2. Results and Discussion

2.1. Construction, Characterization, and Dynamic Transformation
of Pt Ensembles

We constructed Pt ensemble catalysts via a facile wetness im-
pregnation method, using abundant surface ─OH sites and the
spatial barrier eﬀect between NFM-SiO2 layers to dual-conﬁne
Pt species (marked as Pt@NFM-SiO2-400), as illustrated in
Figure 1a. Scanning electron microscopy (SEM) and transmis-
sion electron microscopy (TEM) images (Figures S1 and S2, Sup-
porting Information) reveal that NFM-SiO2 exhibits a 3D lamellar
cross-linked nanoﬂower structure. After loading Pt species and
reducing treatment, the morphology of NFM-SiO2 remained un-
changed (Figure 1b,c). Aberration-corrected scanning transmis-
sion electron microscopy (AC-STEM) shows that the Pt species
are primarily dispersed as sub-nanometric clusters on SiO2 lay-
ers (Figure 1d,e). The mean size of Pt ensembles is measured
at 0.86 nm, with a corresponding structural schematic shown
in Figure 1e. For comparison, closed mesoporous silica spheres
(MCM-41) without lamellar cross-linked structure and conven-
tional silica spheres (SiO2) without mesoporous structure were
also prepared and employed as supports for loading Pt species.
SEM images show that MCM-41 and SiO2 are spherical in shape
(Figures S3 and S4, Supporting Information). The Pt species are
dispersed on both MCM-41 and SiO2 as Pt nanoparticles, with
mean sizes of 2.42 and 2.53 nm, respectively (Figures S5 and S6,
Supporting Information). This indicates that the 3D NFM-SiO2
is beneﬁcial for anchoring and dispersing Pt species into sub-
nanoscale aggregates, thus exposing more active sites. Elemen-
tal energy-dispersive X-ray spectroscopy (EDS) mapping images
conﬁrm a homogeneous distribution of Pt species on the surfaces
of 3D NFM-SiO2, MCM-41, and SiO2 (Figure 1f–i; Figures S7 and
S8, Supporting Information). The inductively coupled plasma op-
tical emission spectrometry (ICP-OES) analysis conﬁrmed that
the Pt content of three samples is as low as ≈0.13 wt.% (Table S1,
Supporting Information).

X-ray diﬀraction (XRD) patterns (Figure S9, Supporting In-
formation) show that all silicon spheres are composed of
amorphous silica. Additionally, the characteristic crystal plane
diﬀraction peaks corresponding to Pt (111) and (200) are ev-
ident in Pt/SiO2,[29] but not detectable in Pt@NFM-SiO2-400

Adv. Sci. 2025, 12, 2415937

2415937 (2 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

Figure 1. a) Schematic illustration for the synthesis, b) SEM, c) TEM, d) AC-TEM, Pt size distribution (inset in ﬁgure d), e) AC-STEM, structure schematic
(inset in ﬁgure e), f) HAADF-STEM, and g–i) EDS-mapping images of Pt@NFM-SiO2-400.

and Pt/MCM-41-400. This observation demonstrates that meso-
porous silicas (NFM-SiO2 and MCM-41) facilitate the dispersion
of Pt species. N2 physical adsorption displays that mean meso-
pore sizes for NFM-SiO2 and MCM-41 are 3.4 and 2.1 nm (Figure
S10 and Table S1, Supporting Information), respectively. Fourier
transform infrared (FT-IR) spectroscopy spectra (Figure S11,
Supporting Information) display a series of characteristic peaks

of typical silica materials, such as isolated SiOH* (3744 cm−1),[30]
Si─OH─Si (3648 cm−1),[31] Si─OH (1627 and 932 cm−1),[30,32,33]
and Si─O─Si (1220, 1042, and 808 cm−1).[34–36] The abundant sil-
icon ─OH groups are more favorable for anchoring and dispers-
ing Pt species.

To understand the eﬀects of temperature on the dynamic
structural transformation of Pt ensembles and to determine the

Adv. Sci. 2025, 12, 2415937

2415937 (3 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

optimal temperature for forming Pt sub-nanometric clusters, we
investigated the surface microstructure changes of Pt@NFM-
SiO2 from 200 to 800 °C using AC-STEM. As shown in Figure S12
(Supporting Information), at a reduction temperature of 200 °C,
some Pt clusters and a few Pt nanoparticles are distributed in
some areas over NFM-SiO2 layers, with a mean size of 1.25 nm.
By increasing the reduction temperature to 300 °C, a substantial
number of Pt nanoparticles and clusters appear on the whole sil-
ica sphere (Figure S13, Supporting Information), with the mean
size of Pt species increasing to 2.13 nm. When the reduction tem-
perature increases to 400 °C, the Pt species are redispersed into
uniform sub-nanometric clusters with a mean size of 0.86 nm
and reach the minimum value (Figure 1d,e). Nevertheless, at a
further elevated reduction temperature of 500 °C, the Pt clusters
aggregated into larger nanoparticles, although a large number
of small Pt clusters remained (Figure S14, Supporting Informa-
tion), resulting in a mean size of 3.44 nm for the Pt species.

Interestingly, as the reduction temperature increases to 600 °C,
larger Pt particles begin to redisperse into smaller Pt particles,
and the number of Pt clusters is decreased, with the mean size
of Pt species dropping to 3.29 nm (Figure S15, Supporting In-
formation). Upon raising the reduction temperature to 700 °C,
Pt species further dispersed into smaller uniform nanoparticles
with a mean size of 2.74 nm (Figure S16, Supporting Informa-
tion), while only a few Pt clusters existed. Conversely, at 800 °C,
Pt clusters disappeared and reaggregated into larger nanoparti-
cles, with a mean size of 3.01 nm (Figure S17, Supporting Infor-
mation). These ﬁndings suggest that the size of Pt ensembles is
temperature-sensitive and undergoes a dynamic transformation
as the temperatures rise, as illustrated in Figure S18 (Supporting
Information). Notably, at temperatures below 700 °C, Pt species
coexist as both nanoclusters and nanoparticles, whereas at tem-
peratures exceeding 700 °C, the nanoclusters disappear and Pt
nanoparticles dominate. Surprisingly, the formation of homoge-
neous sub-nanometric Pt clusters only occurs at an optimal tem-
perature of 400 °C, thereby maintaining or exposing more active
sites.

2.2. Determining the Active Site Types, Coordination, and
Valence State of Pt Ensembles

To further investigate the active site types, coordination, valence
state, and dynamic structural transformation of Pt ensembles
at the atomic level, we combined in situ CO-DRIFTS, X-ray
photoelectron spectroscopy (XPS), X-ray absorption ﬁne struc-
ture (EXAFS), and DFT calculations to clarify Pt site types and
corresponding role in activation chemical bonds. As shown in
Figure 2a, the bands at 2068–2075 cm−1 can be attributed to the
linear adsorption peak of CO on metallic Pt species.[37,38] A pro-
gressive increase in the adsorption intensity of this peak was
noted, accompanied by a shift to higher wavenumbers with the
rising temperature, indicative of the aggregation of Pt species.
It is reported that the peaks at 2027 and 2001 cm−1 can be as-
signed to the vibration modes of gaseous CO adsorbed within
mesoporous channels,[39] and the peaks at 1624 cm−1 can be at-
tributed to CO adsorption on M─O─Si interfacial sites where M
represents metal atoms.[40] To validate these observations, a CO-
DRIFTS adsorption experiment was conducted over NFM-SiO2,

with detailed methodologies outlined in the Supporting Informa-
tion. As can be seen from Figure 2b, four adsorption peaks ap-
peared after adsorption of 2% CO/Ar for 30 min, while only two
adsorption peaks of 2027 and 2001 cm−1 remained after purg-
ing by Ar gas for 10 min. This is because the peaks at 2170 and
2117 cm−1 are ascribed to gas-phase CO molecules,[41] while the
peaks at 2026 and 2001 cm−1 are attributed to strong adsorption
of CO within mesoporous channels. However, the absence of the
CO adsorption peak near 1624 cm−1 prior to Pt species loading
implies CO adsorption on a speciﬁc Pt site.

Previous studies have also shown that CO3

2− is easily ad-
sorbed on the catalyst surface, often resulting in peaks near
1624 cm−1.[42] To exclude this factor, in situ CO2-DRIFTS was
measured over Pt@NFM-SiO2-400 to determine the presence
2− species on the sample surface. As shown in Figure 2c,
of CO3
only gaseous CO2 adsorption peaks (2357 and 2340 cm−1) are
detected,[43] with no peaks at 1624 cm−1, eﬀectively excluding
2− species. These ﬁndings suggest that the
the inﬂuence of CO3
peak at 1624 cm−1 can be attributed to the vibrational mode of
CO adsorption on Pt─O─Si interfacial sites (CO─Pt─O─Si).
Furthermore,
the intensity of this peak diminishes as the
reduction temperature increases, ultimately disappearing at
800 °C. This phenomenon likely results from the cleavage of
the Pt─O─Si bond, coupled with the migration and aggregation
of Pt clusters into larger nanoparticles as temperature rises,
aligning with the AC-STEM results under diﬀerent reduction
temperatures.

XPS spectra were measured to investigate the eﬀects of re-
duction temperature on the state and valence transformation of
Pt ensembles. As shown in Figure S19a (Supporting Informa-
tion), it can be observed that only the Pt2+ species (75.11 and
72.10 eV) can be detected over PtOx@NFM-SiO2.[19,44] After a
reduction treatment (10% H2/Ar) at 200 °C, the Pt 4f7/2 peak
for Pt@NFM-SiO2-200 can be deconvoluted into two peaks at
≈72.20 and 71.28 eV, corresponding to Pt2+ and Pt0 species,
respectively.[19,44] Meanwhile, the ratio of Pt0/(Pt0 + Pt2+) gradu-
ally increases as the temperature rises from 200 to 500 °C (Figure
S19b–e, Supporting Information), suggesting a reduction of the
Pt2+ species to the Pt0, while some PtOx species remain unre-
duced. Subsequently, Pt2+ species are predominantly reduced to
Pt0 after reaching a reduction temperature of 600 °C or higher
(700 and 800 °C; Figure S19f–h, Supporting Information).

To gain insight into the elemental coordination, electronic
state, and bonding structure of Pt ensembles on the surface of
Pt@NFM-SiO2 catalysts, X-ray absorption near-edge structure
(XANES) and extended X-ray absorption ﬁne structure (EXAFS)
tests were performed on Pt@NFM-SiO2-200 and Pt@NFM-SiO2-
400 samples. As shown in Figure 2d, the overall trend of the
Pt L3-edge XANES spectra of Pt@NFM-SiO2-200 and Pt@NFM-
SiO2-400 samples is similar to that of metal Pt foil, suggesting
the existence of Pt0 species. Furthermore, the white line peak
(11570 eV) can be used to determine the change of valence state
in Pt species, with higher valence states corresponding to in-
creased peak intensity.[45] The peak intensity of Pt@NFM-SiO2-
200 exceeds that of Pt@NFM-SiO2-400, suggesting that the Pt
ensembles in Pt@NFM-SiO2-200 exhibit a higher valence state
than Pt@NFM-SiO2-400, and some PtOx species remained unre-
duced, consistent with the XPS results. The Pt L3-edge EXAFS
spectra (Figure 2e–g), reveal the existence of Pt─O, Pt─Si, and

Adv. Sci. 2025, 12, 2415937

2415937 (4 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

Figure 2. In situ DRIFTS of CO adsorption on a) Pt@NFM-SiO2 (under diﬀerent reduction temperatures) and b) NFM-SiO2. c) In situ DRIFTS of CO2
adsorption on Pt@NFM-SiO2-400. The comparison of Pt L3-edge d) XANES and e) EXAFS spectra. Pt L3-edge EXAFS spectra of f) Pt@NFM-SiO2-200
and g) Pt@NFM-SiO2-400. The wavelet transforms from experimental data for h) Pt foil, i) PtO2, j) Pt@NFM-SiO2-200, and k) Pt@NFM-SiO2-400.

Pt─Pt bonds in both samples. Combining the ﬁtting results
(Table S2, Supporting Information), it is obtained that the Pt─Pt
bond coordination numbers of Pt@NFM-SiO2-200 (3.7 ± 0.1)
and Pt@NFM-SiO2-400 (4.8 ± 0.3) are smaller than the Pt foil
(12) and PtO2 (9.2 ± 0.9), implying a reduction in Pt particle size
and the presence of Pt clusters, as also supported by AC-STEM
results. In addition, the existence of Pt─O and Pt─Si bonds in
both samples implies a robust interaction between Pt and SiO2,
potentially leading to the formation of Pt─O─Si interfacial sites.
Wavelet transform analysis (Figure 2h–k) shows a decrease in
signal intensities for Pt─O and Pt─Si bonds, alongside an in-
crease in Pt─Pt bonds as reduction temperature rises from 200
to 400 °C, signifying a higher degree of reduction for Pt@NFM-
SiO2-400 compared to Pt@NFM-SiO2-200.

Collectively, the AC-STEM, CO-DRIFTS, and EXAFS results
elucidate that the sub-nanometric Pt@NFM-SiO2-400 ensemble

catalyst has multi-type active sites, such as Pt─Pt metal sites and
Pt─O─Si interfacial sites. In the context of formaldehyde oxida-
tion, the reactants, including O2, H2O, and HCHO, and the ad-
sorption/activation mechanism of each reactant at diﬀerent Pt
sites remains unclear. It is signiﬁcant to study the roles of diﬀer-
ent active sites and reactants in the design of high-performance
noble metal Pt catalysts. Therefore, the DFT calculations were
performed to investigate the electronic structure of catalysts and
the adsorption behavior of O2, H2O, and HCHO molecules at
diﬀerent Pt sites. A model comprising 13 Pt atoms was con-
structed (Figure 3a), categorizing the Pt─O─Si site bonded to
SiO2 as the “Interfacial site,” the adjacent Pt site as the “Side
site,” and the topmost metallic Pt site as the “Top site.”. DFT anal-
ysis (Figure 3b) reveals substantial electron transfer between Pt
and SiO2, with electrons migrating from the metallic Pt site to
the Pt─O─Si interfacial site. It implies that Pt and O atoms have

Adv. Sci. 2025, 12, 2415937

2415937 (5 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

Figure 3. a) Pt13 ensembles-SiO2 optimal model and b) corresponding charge density distributions. The c–e) O2, f–h) H2O, and i–k) HCHO molecules
adsorbed on diﬀerent sites, and corresponding adsorption energies and Gibbs free energies.

strong bonding cooperation, and the Pt─O─Si interfacial site can
function as an eﬃcient electron transport channel.

Furthermore, the adsorption characteristics of O2, H2O, and
HCHO molecules at each active site (Figure 3c–k and Figure
S20, Supporting Information) are studied. It shows that O2
exhibits the highest adsorption energy (Ead = −0.5934 eV) at the
top site, with the lowest Gipps free energy of adsorption (ΔG =
−0.3981 eV), indicating a preference for O2 adsorption at this
site. Furthermore, H2O and HCHO demonstrate preferential
adsorption at the Pt─O─Si interfacial site, with H2O showing
the highest adsorption energy (Ead = −1.8614 eV) and lowest
Gipps free energy (ΔG = −1.5031 eV), followed closely by
HCHO (Ead = −1.6282 eV, ΔG = −1.3992 eV). These ﬁndings
indicate the Pt top site mainly serves as the center for O2 adsorp-
tion/activation, while the Pt─O─Si interfacial site is crucial for
the H2O and HCHO adsorption/activation. Based on the above
results, we successfully constructed a Pt ensemble catalyst with
multi-type active sites, which can synergistically accelerate the
activation of various chemical bonds in the HCHO oxidation
reaction.

2.3. Catalytic Performance and High Activity Origins in Pt
Ensemble Sites

To demonstrate the unique advantages and high activity origins
of Pt ensemble catalysts in HCHO oxidation, a series of catalytic
performance tests and characterizations were performed. The ac-
tivity of catalysts for oxidation HCHO was evaluated in an air-ﬂow

containing 100 ppm HCHO with weight hourly space velocity
−1 h−1 and
(WHSV) and relative humidity (RH) of 120 000 mL gcat.
40%, respectively. As shown in Figures 4a and S21 (Supporting
Information), the HCHO conversion over NF-SiO2 is 24%, with
no CO2 selectivity, indicating that NF-SiO2 only adsorbs HCHO.
After loading Pt species, the HCHO conversion and CO2 selec-
tivity are gradually improved over the PtOx@NFM-SiO2 sample
(calcinated under a 20% O2/N2 atmosphere at 400 °C), but it
cannot deeply oxidize HCHO. However, the HCHO oxidation
activity of Pt@NFM-SiO2-400 is signiﬁcantly enhanced after a
10% H2/Ar reduction at 400 °C. It shows that the HCHO con-
version and CO2 selectivity over Pt@NFM-SiO2-400 are both in-
creased to ≈100%, indicating metallic Pt0 species have a higher
HCHO removal eﬀect than oxidized PtOx species. The HCHO
oxidation performance of Pt@NFM-SiO2 samples at diﬀerent re-
duction temperatures was further studied, and the test results
are shown in Figure 4b. It is observed that, compared with the
PtOx@NFM-SiO2 sample, the HCHO conversion increased to
≈61% after 200 °C reduction. Furthermore, when the reduction
temperature increased to 300 °C, the HCHO conversion greatly
increased to ≈100%, and the activity remained stable until 700 °C.
However, the HCHO conversion dramatically decreased to ≈64%
after the temperature rose to 800 °C. Unexpectedly, the CO2 se-
lectivity is maintained at 100% and remained unchanged with
the reduction temperature (Figure S22, Supporting Information).
The results suggest that the reduced Pt@NFM-SiO2 samples can
deeply and eﬃciently oxidize the captured HCHO into CO2 and
H2O, preventing the accumulation of intermediates on the cata-
lyst surface.

Adv. Sci. 2025, 12, 2415937

2415937 (6 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

Figure 4. a) HCHO oxidation over NFM-SiO2, PtOx@NFM-SiO2, and Pt@NFM-SiO2-400. b) HCHO oxidation over Pt@NFM-SiO2 under diﬀerent
reduction temperatures. c) HCHO oxidation, d) Arrhenius plots, e) rate, and f) CO-DRIFTS over Pt@NFM-SiO2-400, Pt/MCM-41-400, and Pt/SiO2-400.
g) Cycling and h) stability test of Pt@NFM-SiO2-400.

To elucidate the inﬂuence of reduction temperature on cata-
lyst activity, a series of characterization analyses were carried out
to investigate the bonding structure, crystal structure, and pore
structure of Pt@NFM-SiO2 at diﬀerent reduction temperatures.
FT-IR analysis (Figure S23, Supporting Information) indicates a
decline in the peak intensities of Si─OH─Si and Si─OH, along-
side an increase in isolated SiOH*, suggesting a reduction in sur-
face ─OH groups that facilitate the dispersion and anchoring of
Pt species, causing the Pt species aggregate and overall types and
quantities of active sites to be reduced. This is consistent with
the above AC-STEM and CO-DRIFTS results of Pt@NFM-SiO2
at diﬀerent temperatures. In addition, the XRD pattern (Figure
S24, Supporting Information) reveals a gradual weakening of
the amorphous SiO2 peak intensity, indicative of a reduction in
Si─OH and Si─OH─Si bonds. Nevertheless, no diﬀraction peaks
corresponding to Pt species are detected, although the tempera-
ture rose to 800 °C, indicating that the Pt species would aggre-
gate but might still be highly dispersed. It can be observed that

the speciﬁc surface area gradually decreases from 470 to 304 m2
g−1 as the temperature rises from 200 to 800 °C, but the loading
of Pt species (≈0.14 wt.%) is almost unchanged (Figure S25 and
Table S1, Supporting Information).

Combining with the AC-STEM, CO-DRIFTS, FT-IR, XRD,
BET, and ICP analyses, it can be concluded that the reduction
temperature range of 200–800 °C unchanged the Pt content but
signiﬁcantly aﬀected the types and quantities of active sites. Al-
though aggregation of Pt species occurs in the range of 300–
700 °C, suﬃcient active sites remain available for eﬃcient deep
oxidation of O2, H2O, and HCHO. However, insuﬃcient reduc-
tion at low temperatures over Pt@NFM-SiO2-200 limits the avail-
ability of metallic Pt sites for O2 activation, while excessive tem-
peratures lead to the loss of Pt─O─Si interfacial sites and reduce
activation sites for H2O and HCHO, ultimately lowering overall
catalytic eﬃciency.

To highlight the unique advantages of the Pt species supported
by NFM-SiO2 mesoporous materials, the HCHO degradation

Adv. Sci. 2025, 12, 2415937

2415937 (7 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

properties of Pt@NFM-SiO2-400, Pt/MCM-41-400, and Pt/SiO2-
400 samples were further compared, and the test results are
shown in Figure 4c and Figure S26 (Supporting Information).
The Pt@NFM-SiO2-400 ensemble catalyst exhibited optimal
HCHO degradation performance, achieving ≈100% conversion
and CO2 selectivity, while Pt/MCM-41-400 and Pt/SiO2-400
demonstrated lower conversion of ≈90%, and declining ac-
tivity and selectivity, indicative of lower stability. Kinetic tests
(Figure 4d,e and Table S3, Supporting Information) were per-
formed to further study the catalytic performance of related
catalysts, and the internal and external diﬀusion have been elim-
inated. It can be found that the Pt@NFM-SiO2-400 ensemble
catalyst has the lowest activation energy (21.4 kJ mol−1) and the
highest reaction rate (r) and turnover frequency (TOF) values
compared with Pt/MCM-41-400 and Pt/SiO2-400. This indicates
that the Pt@NFM-SiO2-400 ensemble catalyst exhibits optimal
HCHO degradation capacity.

In addition, the HCHO oxidation performance of Pt/MCM-41
and Pt/SiO2 after 700 °C high-temperature reduction (marked
as Pt/MCM-41-700 and Pt/SiO2-700) was also tested. It can be
observed that the HCHO oxidation performance of Pt/MCM-
41-700 and Pt/SiO2-700 signiﬁcantly decreased (Figure S27,
Supporting Information). The XRD pattern in Figure S28 (Sup-
porting Information) shows that the obvious diﬀraction peaks of
Pt (111) and Pt (200) crystal planes can be detected on Pt/MCM-
41-700 and Pt/SiO2-700, indicating that Pt/MCM-41 and Pt/SiO2
have poor sintering resistance. In contrast, Pt@NFM-SiO2 main-
tains ≈100% HCHO elimination even after high-temperature
(700 °C) reduction. Based on the above results, it can be proven
that NFM-SiO2 mesoporous material outperforms MCM-41 and
SiO2 in dispersing and anchoring Pt ensemble sites. Therefore,
Pt@NFM-SiO2-400 has better HCHO degradation performance
and sintering resistance. Furthermore, we compared the catalytic
performance for HCHO oxidation of various oxide-supported
Pt catalysts with literature. As shown in Table S4 (Supporting
Information), Pt@NFM-SiO2 exhibits excellent catalytic activity
and stability for HCHO oxidation over the Pt-based catalysts.

To further identify the primary reasons why Pt@NFM-SiO2-
400 ensemble catalyst has optimal catalytic performance com-
pared to Pt/MCM-41-400 and Pt/SiO2-400, the Pt species state,
redox ability, and oxygen/water activation ability were studied.
As shown in Figure S29 (Supporting Information), all samples
showed two valence Pt species (Pt0 and Pt2+). The ratio of Pt0/(Pt0
+ Pt2+) in Pt@NFM-SiO2-400 remained unchanged after the
HCHO oxidation test (marked as Pt@NFM-SiO2-400-used). Nev-
ertheless, the ratio of Pt0/(Pt0 + Pt2+) over Pt/MCM-41-400 and
Pt/SiO2-400 declined from 0.74 and 0.61 to 0.65 and 0.52, re-
spectively, after the HCHO oxidation test (marked as Pt/MCM-
41-400-used and Pt/SiO2-400-used). These results indicate that
Pt@NFM-SiO2-400 has excellent oxidation resistance at low tem-
peratures owing to the dual conﬁnement eﬀect of NFM-SiO2.
The CO-DRIFTS spectra (Figure 4f) show that two types of Pt
sites can be observed at Pt@NFM-SiO2-400: metallic Pt site (2068
cm−1) and Pt─O─Si interfacial site (1624 cm−1). In contrast, only
metallic Pt sites (2070 and 2077 cm−1) were detected in Pt/MCM-
41-400 and Pt/SiO2-400, and the peak intensity is weaker than
Pt@NFM-SiO2-400. This result suggests that the Pt@NFM-SiO2-
400 ensemble catalyst can expose more types of active sites to ox-
idation HCHO.

In the H2-TPR test, as shown in Figure S30 (Supporting Infor-
mation), the positive peaks at 40–103 °C are attributed to the re-
duction of Pt2+ to Pt0,[46] and the negative peaks at 86–133 °C are
associated with the decomposition of PtHx.[47] It can be clearly
observed that the Pt2+ reduction peak and PtHx decomposition
peak of Pt@NFM-SiO2-400 are the lowest, implying that it has
optimal reducibility. The peaks at 480–504 °C corresponded to
the reduction of bulk PtOx to metallic Pt,[47] and the peak inten-
sity is minimum over Pt@NFM-SiO2-400. The results revealed
that there are barely large Pt particles on the Pt@NFM-SiO2-
400 surface, existing instead as tiny nanoclusters, which aligns
with the AC-STEM results (Figure 1d,e). As can be seen in the
O2-TPO test (Figure S31, Supporting Information), the negative
peaks at 94–111 °C can be attributed to the desorption peak of
chemisorbed oxygen.[48,49] Among the catalysts, Pt@NFM-SiO2-
400 has the lowest desorption temperature, indicating its en-
hanced O2 activation capability. In addition, the peaks at 230 and
488 °C are attributed to the oxidation of surface and bulk metallic
Pt species, respectively.[50] The peak at 625 °C is assigned to the
re-decomposition of PtOx species into metallic Pt and O atoms.
The results of H2-TPR and O2-TPO show that Pt@NFM-SiO2-400
has better redox ability.

− and O2

To gain a deeper insight into the catalyst activation gaseous O2
and H2O capacity and the dynamic changes of reactive oxygen
species on catalyst surfaces, we carried out the EPR, O2-DRIFTS,
and H2O-DRIFTS studies. As shown in Figure S32 (Supporting
−) species could be detected at a
Information), the superoxide (O2
g value of 2.016.[51] O2-DRIFTS (Figure S33, Supporting Informa-
tion) that the bonds at 974, 980, and 984 cm−1 could be attributed
− species,[52] consistent with the EPR results. Furthermore,
to O2
2−) were observed at 885, 886, and 907
the peroxide species (O2
cm−1.[52] The relative intensities (Figure S33d, Supporting Infor-
2−) on
mation) of surface reactive oxygen species (O2
Pt@NFM-SiO2-400 reached their highest levels after 30 min of
O2 adsorption, indicating Pt@NFM-SiO2-400 has the better O2
activation capacity. In the H2O-DRIFTS (Figure S34, Support-
ing Information), absorption peaks at 3662–3673 cm−1 can be
attributed to surface ─OH vibrations, while the vibration peaks
at 3216–3268 cm−1 can be attributed to the absorbed H2O.[53]
As can be seen from Figure S34d (Supporting Information), it
proved that Pt@NFM-SiO2-400 has the better H2O activation ca-
pacity due to the highest levels of ─OH species after 30 min of
H2O adsorption. Based on the above characterization results, the
Pt@NFM-SiO2-400 ensemble catalyst exhibits the best HCHO
catalytic oxidation performance, which can be attributed to the
satisfactory oxidation resistance and more Pt site types and quan-
tities, as well as the better redox capacity. This accelerates the O2
and H2O adsorption/activation to form abundant reactive oxygen
2−, and ─OH), which achieved the eﬃcient and
−, O2
species (O2
deep degradation of HCHO.

Additionally, the service life of the Pt@NFM-SiO2-400 ensem-
ble catalyst was measured at diﬀerent test conditions to evaluate
its potential application value. As shown in Figure S35a (Sup-
porting Information), at a relative humidity (RH) is 40%, the
HCHO conversion reaches ≈100%. Subsequently, a slight de-
crease in conversion was observed when RH dropped to 20%,
and a signiﬁcant decline occurred at 10% RH. This decline might
be due to insuﬃcient surface ─OH species for the HCHO oxi-
dation under low RH conditions, causing a decrease in catalyst

Adv. Sci. 2025, 12, 2415937

2415937 (8 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

activity. Amazingly, the HCHO conversion recovered to 100% af-
ter the RH rose back to 40%, indicating that Pt@NFM-SiO2-400
has excellent regeneration. However, the HCHO conversion al-
most remained unchanged under high humidity RHs of 60%
and 80%, demonstrating Pt@NFM-SiO2-400 has excellent mois-
ture resistance and can eﬃciently adsorb and activate H2O. It
can be observed that the CO2 selectivity (Figure S35b, Support-
ing Information) is maintained at ≈100% under diﬀerent hu-
midity conditions, illustrating HCHO can be deeply oxidized to
CO2 and H2O over the Pt@NFM-SiO2-400 surface. As shown
in Figure S36 (Supporting Information), the catalytic oxidation
performance of HCHO over Pt@NFM-SiO2-400 remained un-
changed at various concentrations. It implies that the Pt@NFM-
SiO2-400 catalyst has broad adaptability to HCHO concentra-
tions. Furthermore, the HCHO conversion (Figure S37a, Sup-
porting Information) decreased after the WHSV was increased to
−1 h−1, owing to the short residence
240000 and 360000 mL gcat.
time of the reactants at high WHSV and insuﬃcient contact
time with the active sites. However, the CO2 selectivity (Figure
S37b, Supporting Information) still remained ≈100%, indicating
the Pt@NFM-SiO2-400 catalyst could deeply oxidize the captured
HCHO molecules. As shown in Figure S38 (Supporting Infor-
mation), the HCHO conversion and CO2 selectivity maintained
≈100% with the temperature change (25–80 °C). This result in-
dicates that Pt@NFM-SiO2-400 has excellent adaptability to am-
bient temperatures. The cyclic and long-term stability tests were
also performed to study the durability of Pt@NFM-SiO2-400. As
shown in Figure 4g and Figure S39 (Supporting Information), the
HCHO conversion and CO2 selectivity still maintain ≈100% after
ﬁve cyclic tests, indicating that Pt@NFM-SiO2-400 has excellent
durability. After a 3360-min test, the HCHO removal eﬃciency
remains at ≈98% (Figure 4h), further conﬁrming excellent dura-
bility and potential application value for the Pt@NFM-SiO2-400
ensemble catalyst.

2.4. Reaction Mechanism Studies

To determine the HCHO oxidation reaction pathways over
Pt@NFM-SiO2-400, in situ DRIFTS spectra were used to study
the reaction intermediates. The detailed testing procedures are
presented in the Supporting Information, and the assigned re-
sults are present in Table S5 (Supporting Information). As shown
in Figure 5a, after exposure to N2 + HCHO (100 ppm) for 30 min,
the absorption vibration peak of HCHO (1723 cm−1) and some
typical intermediate species vibration peaks can be detected.[54]
Such as surface ─OH (3662 cm−1),[53] H2O (3218 cm−1),[53]
CO (2068 cm−1),[37,38] DOM (1176 and 1028 cm−1),[6,53,55,56] and
HCOO− (1624 cm−1) species.[6,53,55,56] It is evident that the peak
intensities of CO, DOM, and HCOO− species gradually in-
creased, but the peak intensities of H2O and ─OH ﬁrst increased
and then decreased. This indicates that the surface ─OH of the
catalyst is involved in HCHO oxidation in the absence of O2 and
H2O. And the H2O from the product will be re-activated into
─OH to participate in the reaction, causing peak intensities to
increase and then weaken.

After the atmosphere is switched to O2 + N2 + HCHO, as
shown in Figure 5b, the intermediate species types of ─OH
(3662 cm−1), CO (2072 cm−1), DOM (1172 and 1031 cm−1), and

HCOO− (1624 cm−1) remained unchanged. However, the peak
intensities of CO are weaker than those in Figure 5a, indicat-
ing that gaseous O2 plays an indispensable role in HCHO oxida-
−
tion. Since O2 can provide additional reactive oxygen species (O2
2−) to accelerate the degradation of intermediate species.
and O2
Furthermore, after the atmosphere is switched to H2O + N2 +
HCHO (RH = 40%; Figure 5c), an increase in the number of
DOM peaks (1434, 1303, 1180, and 1031 cm−1) and a stronger
CO peak (2058 cm−1) were observed, indicating that the ─OH
species activated by physical adsorption water participated in the
HCHO oxidation, and H2O also plays a vital role. Surprisingly,
the peaks of the intermediate species CO disappear after the re-
action atmosphere is switched to O2 + H2O + N2 + HCHO (RH
= 40%), as shown in Figure 5d, and only the ─OH (3662 cm−1),
DOM (1300, 1173, and 1035 cm−1) and HCOO− (1624 cm−1) can
be observed. It is demonstrated that the simultaneous presence
of O2 and H2O can change the HCHO oxidation reaction path-
way.

−, O2
− and O2

Based on the above results, in the HCHO reaction system,
either O2 or H2O alone is unfavorable to the HCHO oxidative
degradation and follows a CO-containing path: HCHO → DOM
→ HCOO− → CO → CO2. Only when the simultaneous existence
of O2 and H2O can provide suﬃcient reactive oxygen species
2−, and ─OH) for the HCHO oxidation. Among them,
(O2
2− species mainly activate the initial HCHO into
O2
DOM, and then ─OH oxidizes the DOM into HCOO−, ﬁnally
oxidized to CO2 and H2O. The reactive oxygen species synergis-
tically promote HCHO oxidation, thus shortening the HCHO ox-
idation pathway and improving catalytic eﬃciency. Furthermore,
the HCHO activity tests under diﬀerent atmospheres (Figure 5e)
show that Pt@NFM-SiO2-400 has poor HCHO oxidation activity
under O2 or H2O alone. It is clearly found that Pt@NFM-SiO2-
400 has excellent HCHO oxidation performance under the simul-
taneous existence of O2 and H2O. This result further proved that
2−, and ─OH produced by O2
−, O2
the reactive oxygen species O2
and H2O synergistically promoted the eﬃcient deep oxidation of
HCHO. The possible reaction pathways of HCHO oxidation over
Pt@NFM-SiO2-400 are shown in Figure 5f.

To further clarify the O2, H2O, and HCHO oxidation reac-
tion mechanisms, as well as the evolution process of interme-
diate species over the Pt@NFM-SiO2-400 surface. DFT calcula-
tions were performed to study the reaction pathways and free en-
ergies of O2, H2O, and HCHO activation. As shown in Figure
*
5g, O2 is preferentially adsorbed at the top site to form O2
* species are activated into two
species. Subsequently, these O2
O* species, and then one O* species reacts with H2O* adsorbed
at the Pt─O─Si interfacial site to form two OH* species. Among
them, TS1 (Ea = 0.49 eV) has the highest energy barrier, which
is the rate-determining step of the O2 and H2O activations. Fur-
thermore, the reaction pathway involving reactive oxygen species
(O* and OH*) in the synergistic oxidation of HCHO was cal-
culated, as shown in Figure 5h. First, O* species reacts with
*
HCHO* adsorbed at the Pt─O─Si interface site to form CH2O2
species, which is further transformed into HCOOH* species.
Then, HCOOH* reacts with OH* to produce COOH* species. Fi-
nally, COOH* reacts with OH* to produce CO2 and H2O. Among
the four transition states, TS3 (Ea = 0.66 eV) presents the high-
est energy barrier. This ﬁnding indicates that HCOOH* react-
ing with OH* to form COOH* is the rate-determining step of

Adv. Sci. 2025, 12, 2415937

2415937 (9 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

Figure 5. In situ DRIFTS spectra of HCHO oxidation over Pt@NFM-SiO2-400 under diﬀerent reaction atmospheres: a) N2 + HCHO, b) O2 + N2 +
HCHO, c) H2O + N2 + HCHO, and d) O2 + H2O + N2 + HCHO. e) HCHO conversion over Pt@NFM-SiO2-400 under diﬀerent reaction atmospheres.
f) Possible reaction pathways of HCHO oxidation over Pt@NFM-SiO2-400. Gibbs free energy calculations for g) O2 and H2O active, and h) HCHO
oxidation.

HCHO oxidation. Therefore, experimental results and DFT cal-
culations clearly demonstrate a dual-synergistic eﬀect exists in
HCHO oxidation over the Pt@NFM-SiO2-400 surface. Initially,
Pt top sites and Pt─O─Si interfacial sites can synergistically pro-
mote the activation of O2 and H2O to generate abundant reactive
2−, and
oxygen species (O2
─OH species further synergistically enhance the degradation of
key intermediate species (DOM and HCOO−) to CO2 and H2O.

2−, and ─OH), and then O2

−, O2

−, O2

3. Conclusion

In summary, we successfully synthesized sub-nanometric Pt en-
sembles with multi-type active sites through a dual-conﬁnement
strategy, where these sites can synergistically accelerate reac-

tant activation. The size of Pt ensembles undergoing dynamic
transformation between clusters and nanoparticles at diﬀerent
reduction temperatures. The smallest sub-nanometer Pt clusters
are obtained at a reduction temperature of 400 °C, which has op-
timal redox ability, catalytic activity, durability, and adaptability to
various working conditions in HCHO oxidation. In addition, CO-
DRIFTS and EXAFS demonstrated that the Pt ensembles have
multi-type active sites, including Pt─Pt metal sites and Pt─O─Si
interface sites. DFT calculation results prove that diﬀerent Pt
sites play diﬀerent roles in the activation of chemical bonds.
Particularly, the Pt top site is the O2 activation center, while
the Pt─O─Si interfacial site is the HCHO and H2O activation
−,
centers. The mechanism study showed that the generated O2
2−, and ─OH from the activation of O2 and H2O synergistically
O2

Adv. Sci. 2025, 12, 2415937

2415937 (10 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

facilitated the eﬀective catalytic oxidation of HCHO and short-
ened the reaction pathway. This study not only established
the controllable preparation method of high-performance Pt
ensemble catalysts but also helped us understand the roles of
diﬀerent metal active sites in heterogeneous catalysts.

Supporting Information

Supporting Information is available from the Wiley Online Library or from
the author.

Acknowledgements

This work was supported by the National Natural Science Foundation of
China (22276223 and 22076224) and Shenzhen Science and Technology
Innovation Program (No. CJGJZD20220517142401004).

Conﬂict of Interest

The authors declare no conﬂict of interest.

Data Availability Statement

The data that support the ﬁndings of this study are available in the sup-
plementary material of this article.

Keywords

heterogeneous catalysis, multi-type active sites, Pt ensembles, reactive
oxygen species

Received: November 29, 2024
Revised: January 25, 2025
Published online: February 18, 2025

[13] Y. Si, Y. Jiao, M. Wang, S. Xiang, J. Diao, X. Chen, J. Chen, Y. Wang, D.
Xiao, X. Wen, N. Wang, D. Ma, H. Liu, Nat. Commun. 2024, 15, 4887.
[14] Z. Zhang, G. He, Y. Li, C. Zhang, J. Ma, H. He, Environ. Sci. Technol.

2022, 56, 10916.

[15] G. Xie, W. Guo, Z. Fang, Z. Duan, X. Lang, D. Liu, G. Mei, Y. Zhai, X.

Sun, X. Lu, Angew. Chem., Int. Ed. 2024, 63, e202412568.

[16] H. Wang, L. Wang, D. Lin, X. Feng, Y. Niu, B. Zhang, F. Xiao, Nat.

Catal. 2021, 4, 418.

[17] F. Meng, L. Zhu, R. Li, J. Jiang, Y. Li, Y. Wu, Y. Fan, P. Ren, H. Xu,
D. Wang, J. Zhang, M. An, P. Yang, Adv. Funct. Mater. 2024, https:
//doi.org/10.1002/adfm.202416678.

[18] Z. Luo, G. Zhao, H. Pan, W. Sun, Adv. Energy Mater. 2022, 12,

2201395.

[19] S. Kaiser, J. Plansky, M. Krinninger, A. Shavorskiy, S. Zhu, U. Heiz, F.

Esch, B. A. J. Lechner, ACS Catal. 2023, 13, 6203.

[20] B. Zhang, J. Wang, G. Liu, C. M. Weiss, D. Liu, Y. Chen, L. Xia, P. Zhou,
M. Gao, Y. Liu, J. Chen, Y. Yan, M. Shao, H. Pan, W. Sun, Nat. Catal.
2024, 7, 441.

[21] W. Wang, E. J. G. Santos, B. Jiang, E. Cubuk, C. Ophus, A. Centeno, A.
Pesquera, A. Zurutuza, J. Ciston, R. Westervelt, E. Kaxiras, Nano Lett.
2014, 14, 450.

[22] C. Wang, J. Wang, X. Liu, Y. Li, C. Zhang, Y. Zheng, W. Shan, Catal. Sci.

Technol. 2023, 13, 6409.

[23] L. Liu, A. Corma, Trends Chem. 2020, 2, 383.
[24] M. Hu, X. Liang, S. Liu, Z. Cai, F. Shen, S. Yang, Z. Wang, G. Sun, H.
Ren, Y. Cao, S. Wang, S. Zhao, K. Zhou, Chem. Mat. 2023, 35, 5204.
[25] N. Wang, Q. Sun, R. Bai, X. Li, G. Guo, J. Yu, J. Am. Chem. Soc. 2016,

138, 7484.

[26] H. Peng, X. Zhang, X. Han, X. You, S. Lin, H. Chen, W. Liu, X. Wang,
N. Zhang, Z. Wang, P. Wu, H. Zhu, S. Dai, ACS Catal. 2019, 9, 9072.
[27] C. Xu, G. Chen, Y. Zhao, P. Liu, X. Duan, L. Gu, G. Fu, Y. Yuan, N.

Zheng, Nat. Commun. 2018, 9, 3367.

[28] Y. Zhang, J. Zhang, B. Zhang, R. Si, B. Han, F. Hong, Y. Niu, L. Sun,
L. Li, B. Qiao, K. Sun, J. Huang, M. Harut, Nat. Commun. 2020, 11,
558.

[29] R. Peng, X. Sun, S. Li, L. Chen, M. Fu, J. Wu, D. Ye, Chem. Eng. J. 2016,

306, 1234.

[30] B. B. Burton, S. W. Kang, S. W. Rhee, S. M. George, J. Phys. Chem. C

2009, 113, 8249.
J. Datka, B. Gil, P. Baran, Micropor. Mesopor. Mater. 2003, 58, 291.

[31]
[32] B. Cheng, X. Wang, L. Wang, Y. Wu, Mater. Lett. 2007, 61, 1350.
[33] U. Baig, M. Faizan, M. A. Dastageer, M. A. Gondal, Chemosphere

2022, 308, 136405.

[1]

J. Zhang, M. Wang, Z. Gao, X. Qin, Y. Xu, Z. Wang, W. Zhou, D. Ma,
J. Am. Chem. Soc. 2022, 144, 5108.

[2] M. Peng, C. Dong, R. Gao, D. Xiao, H. Liu, D. Ma, ACS Cent. Sci. 2020,

[34] F. Lu, R. Wright, P. Lu, P. C. Cvetic, P. R. Ohodnicki, Sens. Actuators, B

2021, 340, 129853.

[35] M. Sitarz, M. Handke, W. Mozgawa, Spectrochim. Acta. A 2000, 56A,

7, 262.

1819.

[3] W. M. H. Sachtler, R. A. Van Santen, Adv. Catal. 1977, 26, 69.
[4]

J. Wang, G. He, C. Wang, X. Chen, X. Liu, Y. Li, W. Shan, H. He, Appl.
Catal. B Environ. Energy 2024, 347, 123787.

[5] Y. Li, T. Dong, P. Huang, J. Ji, H. Huang, Appl. Catal. B Environ. Energy

[36] S. B. Vishwakarma, S. K. Dubey, R. L. Dubey, A. Yadav, V. Jadhav, V.
Bambole, I. Sulania, D. Kanjilal, K. D. Devi, Radiat. Eﬀ. Defects Solids
2020, 175, 695.

[37] X. Ye, H. Wang, Y. Lin, X. Liu, L. Cao, J. Gu, J. Lu, Nano Res. 2019, 12,

2024, 341, 123322.

[6] T. Dong, J. Ji, L. Yu, P. Huang, Y. Li, Z. Suo, B. Liu, Z. Hu, H. Huang,

JACS Au 2023, 3, 1230.

[7] Q. Yu, S. Wang, M. Wang, X. Mou, R. Lin, Y. Ding, Chin. J. Catal. 2022,

43, 820.

[8] W. Yuan, K. Fang, R. You, Z. Zhang, Y. Wang, Acc. Mater. Res. 2023, 4,

275.

[9] L. Liu, A. Corma, Chem 2021, 7, 2347-.
[10] L. Liu, A. Corma, Nat. Rev. Mater. 2021, 6, 244.
[11] C. Dong, Z. Gao, Y. Li, M. Peng, M. Wang, Y. Xu, C. Li, M. Xu, Y. Deng,
X. Qin, F. Huang, X. Wei, Y. Wang, H. Liu, W. Zhou, D. Ma, Nat. Catal.
2022, 5, 485.

[12] Y. Li, L. Guo, M. Du, C. Tian, G. Zhao, Z. Liu, Z. Liang, K. Hou, J.

Chen, X. Liu, L. Jiang, B. Nan, L. Li, Nat. Commun. 2024, 15, 5598.

1401.

[38] A. I. Serykh, O. P. Tkachenko, V. Y. Borovkov, V. B. Kazansky, M.
Beneke, N. I. Jaeger, G. Schulz-Ekloﬀ, Phys. Chem. Chem. Phys. 2000,
2, 5647.
I. Lee, Q. Zhang, J. Ge, Y. Yin, F. Zaera, Nano Res. 2011, 4, 115.
[39]
[40] Y. Wang, Z. Song, D. Ma, H. Luo, D. Liang, X. Bao, J. Mol. Catal. A,

[41]

Chem. 1999, 149, 51.
J. Zhang, Y. Pan, D. Feng, L. Cui, S. Zhao, J. Hu, S. Wang, Y. Qin, Adv.
Mater. 2023, 35, 2300902.

[42] Z. Zhou, J. Zhang, Y. Liu, Fuel 2024, 359, 130434.
[43] G. Li, N. Li, Y. Sun, Y. Qu, Z. Jiang, Z. Zhao, Z. Zhang, J. Cheng, Z.

Hao, Appl. Catal. B Environ. Energy 2021, 282, 119512.

[44] Y. Li, Z. Wu, C. Wang, X. Yu, W. Gao, B. Wang, C. Wu, Y. Yao, J. Yang,

Z. Zou, Adv. Funct. Mater. 2024, 34, 2310428.

Adv. Sci. 2025, 12, 2415937

2415937 (11 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

www.advancedsciencenews.com

www.advancedscience.com

[45] Z. Lin, Z. Wang, J. Gong, T. Jin, S. Shen, Q. Zhang, J. Wang, W. Zhong,

[51] Y. Sun, J. Xu, X. Xu, X. Fang, Y. Guo, R. Liu, W. Zhong, X. Wang, Ind.

Adv. Funct. Mater. 2023, 33, 2307510.

Eng. Chem. Res. 2020, 59, 9382.

[46] Y. Liu, Y. Zhou, Q. Ke, M. Lu, W. Zhou, G. Cui, X. Weng, H. Lu, Appl.

[52] M. Chen, Y. Qiu, W. Wang, X. Li, J. Wang, H. Wen, Z. Yang, P. Wang,

Catal. A Gen. 2022, 639, 118642.

[47] B. Wang, B. Chen, Y. Sun, H. Xiao, X. Xu, M. Fu, J. Wu, L. Chen, D. Ye,

[53]

Appl. Catal. B Environ. Energy 2018, 238, 328.

J. Hazard. Mater. 2021, 416, 126224.
J. Ye, M. Zhou, Y. Le, B. Cheng, J. Yu, Appl. Catal. B Environ. Energy
2020, 267, 118689.

[48] Z. Zou, M. Meng, Q. Li, Y. Zha, Mater. Chem. Phys. 2008, 109, 373.
[49] B. Yue, R. Zhou, Y. Wang, X. Zheng, J. Mol. Catal. A Chem. 2005, 238,

[54] Y. Li, X. Chen, C. Wang, C. Zhang, H. He, ACS Catal. 2018, 8, 11377.
[55] C. Wang, Y. Li, L. Zheng, C. Zhang, Y. Wang, W. Shan, F. Liu, H. He,

241.

ACS Catal. 2021, 11, 456.

[50] P. Castellazzi, G. Groppi, P. Forzatti, Appl. Catal. B Environ. Energy

[56] C. Wang, Y. Li, C. Zhang, X. Chen, C. Liu, W. Weng, W. Shan, H. He,

2010, 95, 303.

Appl. Catal. B Environ. Energy 2021, 282, 119540.

Adv. Sci. 2025, 12, 2415937

2415937 (12 of 12)

© 2025 The Author(s). Advanced Science published by Wiley-VCH GmbH

