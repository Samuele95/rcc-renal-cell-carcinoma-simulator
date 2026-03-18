% -----------------------------------------------------------------------------
% LaTeX Class 'unicam_thesis' - LaTeX class for composing MSc and BSc thesis
%
% Andrea Polini <andrea.polini@unicam.it>
% Francesco De Angelis <francesco.deangelis@unicam.it>
%
% Adapted for English by Samuele Stronati, 2026.
% -----------------------------------------------------------------------------

% -----------------------------------------------------------------------------
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{unicam_thesis}[2010/06/30 - LaTeX class for composing thesis at
University of Camerino - School of Science and Technologies]
% -----------------------------------------------------------------------------

\newcommand{\@ptoption}{1pt}
\newcommand{\@tipo}{twoside}
\ExecuteOptions{oneside,12pt}
\ProcessOptions\relax
\typeout{*************************************************************************}
\typeout{****** Document Class 'unicam_thesis' <June 30, 2010> *******************}
\typeout{****** Please report bugs, comments, suggestions, and improvements ******}
\typeout{****** to Andrea Polini <andrea.polini@unicam.it> ***********************}
\typeout{****** or Francesco De Angelis <francesco.deangelis@unicam.it> **********}
\typeout{*************************************************************************}
% -----------------------------------------------------------------------------
% Load the book class for a4 paper dimension
% -----------------------------------------------------------------------------
\LoadClass[\@tipo,a4paper,1\@ptoption]{book}

% -----------------------------------------------------------------------------
% Load support packages
% -----------------------------------------------------------------------------

% set page geometry
\RequirePackage[top=3cm, bottom=3cm, inner=3.5cm, outer=3cm]{geometry}%

% character encoding
\RequirePackage[utf8]{inputenc}%

\RequirePackage{graphicx}%
\RequirePackage{makeidx}%
\RequirePackage{wrapfig}%
\RequirePackage{arydshln}%
\RequirePackage{amssymb}%
\RequirePackage{amsmath}%
\RequirePackage{amsthm}%
\PassOptionsToPackage{hyphens}{url}\RequirePackage[bookmarks=true,colorlinks=true,linkcolor=black,citecolor=black,urlcolor=black]{hyperref}%
\RequirePackage{subfig}%
\RequirePackage{xspace}%
\RequirePackage{array}%
\RequirePackage{times}%
\RequirePackage{fancyhdr}%
\pagestyle{fancy}%

\setlength{\headheight}{15pt}
\renewcommand{\sectionmark}[1]{\markright{#1}{}} \fancyhf{}
\fancyhead[LE]{\textit{\nouppercase{\rightmark}}}
\fancyhead[RO]{\textit{\nouppercase{\rightmark}}}
\fancyfoot[LE,RO]{\thepage}

\fancypagestyle{plain}{ %
	\fancyhf{} %
	\renewcommand{\headrulewidth}{0pt}%
	\renewcommand{\footrulewidth}{0pt}%
}

\renewcommand{\familydefault}{\rmdefault}
\renewcommand{\rmdefault}{cmr}

% English labels
\renewcommand\figurename{Figure}
\renewcommand\tablename{Table}
\renewcommand\contentsname{Contents}

\makeindex %
\date{} %

\RequirePackage[english]{varioref}
\RequirePackage[english]{babel}
\RequirePackage{colortbl}

% Bibliography (natbib for \citep / \citet commands)
\RequirePackage[numbers,sort&compress]{natbib}

\RequirePackage{listings}
\definecolor{listingsBackground}{rgb}{0.9,0.9,0.9}
\lstdefinestyle{pythonCode}{language=Python,frame=tbrl,
	basicstyle=\scriptsize\ttfamily,keywordstyle=\ttfamily\bf,
	stringstyle=\itshape,flexiblecolumns=true,
	commentstyle=\itshape,captionpos=b,abovecaptionskip=10pt,belowcaptionskip=0pt,
	backgroundcolor=\color{listingsBackground}, frame=none
	, numbers=left, numberstyle={\tiny }
}

% ---------------------------------------------------------------------------
% --- Numbering
% ---------------------------------------------------------------------------
\setcounter{secnumdepth}{3}

% ---------------------------------------------------------------------------
% --- Empty pages...
% ---------------------------------------------------------------------------

\let\origdoublepage\cleardoublepage
\newcommand{\clearemptydoublepage}{%
	\clearpage
	{\pagestyle{empty}\origdoublepage}%
}
\let\cleardoublepage\clearemptydoublepage


% ---------------------------------------------------------------------------
% --- FRONTPAGE
% ---------------------------------------------------------------------------
\newcommand{\mychaptertitlefont}{\fontseries{s}\fontsize{20}{24}\selectfont}
\newcommand{\mytitlefont}{\fontseries{b}\sc\fontsize{15}{24}\selectfont}
\newcommand{\mysubtitlefont}{\fontseries{s}\fontsize{13}{16}\selectfont}
\newcommand{\authorfont}{\fontseries{s}\fontsize{14}{14}\selectfont}
\newcommand{\largefont}{\fontseries{s}\fontsize{18}{14}\selectfont}
\newcommand{\bigfont}{\fontseries{s}\fontsize{20}{14}\selectfont}
\newcommand{\biggerfont}{\fontseries{s}\fontsize{26}{22}\selectfont}

\def\author#1{\gdef\@theauthor{#1}}
\def\university#1{\gdef\@theuniversity{#1}}
\def\school#1{\gdef\@theschool{#1}}
\def\course#1{\gdef\@thecourse{#1}}
\def\advisor#1{\gdef\@theadvisor{#1}}
\def\secondadvisor#1{\gdef\@thesecondadvisor{#1}}
\global\let\@thesecondadvisor\@empty
\def\thirdadvisor#1{\gdef\@thethirdadvisor{#1}}
\global\let\@thethirdadvisor\@empty
\def\academicyear#1{\gdef\@theacademicyear{#1}}
\def\matricola#1{\gdef\@thematricola{#1}}
\def\contacta#1{\gdef\@thecontacta{#1}}
\global\let\@thecontacta\@empty

\def\title#1{\gdef\@thetitle{#1}}
\def\subtitle#1{\gdef\@thesubtitle{#1}}

\def\@theauthors{}
\def\@thetitle{}
\def\@thesubtitle{}

\newcommand{\HRule}{\rule{\linewidth}{0pt}}

\renewcommand{\maketitle}{%
	\thispagestyle{empty}
	\setlength{\parindent}{0mm}
	\setlength{\parskip}{0mm}

	\begin{center}
		\includegraphics[width=2.5cm]{images/logo}\par%
		\vspace{0.4cm}%
		{\rmfamily \Large \bfseries \@theuniversity \par}%
		\vspace{0.54cm}%
		\hrule%
		\vspace{0.54cm}%
		{\rmfamily \Large \scshape School of \@theschool \par}%
		\vspace{0.15cm}%
		{\rmfamily \large \@thecourse \par}%
		\vspace*{\stretch{7}}%
		{\rmfamily \LARGE \bfseries \@thetitle \par}%
		\vspace*{\stretch{7}}%
	\end{center}%
	% --- Candidate / Advisor block (outside center to allow \hfill) ---
	\noindent\makebox[\textwidth]{Candidate \hfill Advisor}\\[4pt]%
	\noindent\makebox[\textwidth]{\bfseries \large \@theauthor \hfill \@theadvisor}\\[2pt]%
	\noindent\makebox[\textwidth]{\bfseries \small Student ID \@thematricola \hfill}%
	\ifx\@thecontacta\@empty
		\relax
	\else
		\\[1pt]\noindent\makebox[\textwidth]{\small \texttt{\@thecontacta} \hfill}%
	\fi
	% Second advisor if present
	\ifx\@thesecondadvisor\@empty
		\relax
	\else
		\\[0.8cm]\noindent\makebox[\textwidth]{\hfill Co-Advisor}\\[4pt]%
		\noindent\makebox[\textwidth]{\hfill \bfseries \large \@thesecondadvisor}%
	\fi
	% Third advisor if present
	\ifx\@thethirdadvisor\@empty
		\relax
	\else
		\\[0.8cm]\noindent\makebox[\textwidth]{\hfill Second Co-Advisor}\\[4pt]%
		\noindent\makebox[\textwidth]{\hfill \bfseries \large \@thethirdadvisor}%
	\fi
	%
	\vspace*{\stretch{7}}%
	\begin{center}
		\hrule%
		\vspace{0.54cm}%
		{\large A.Y. \@theacademicyear}%
	\end{center}

	\newpage
	\setlength{\parindent}{1em}
	\setlength{\parskip}{2pt}
	\cleardoublepage
}



% ---------------------------------------------------------------------------
%    Headers
% ---------------------------------------------------------------------------
\pagestyle{fancy}

% ---------------------------------------------------------------------------
% --- MISC COMMANDS
% ---------------------------------------------------------------------------

\def\date#1{\gdef\@thedate{#1}}

\newcommand{\abstract}[1]{
	\newpage
	\noindent
	\fbox{\parbox{.98\linewidth}{
		\vspace{-5mm}
		\section*{Abstract}
		\par
		#1
		}}\\[1cm]}
\newcommand{\keywords}[1]{
	\noindent\fbox{\parbox{.98\linewidth}{
		\vspace{-5mm}
		\section*{Keyword List }
		\par
		#1
	}}
}

\setlength{\baselineskip}{17pt}

\newcommand{\acronym}[2]{
	#1 & #2 \\ \hline
}
\newenvironment{acronyms}
{
	\newpage
	\chapter*{Table of Acronyms}
	\addcontentsline{toc}{chapter}{Table of Acronyms}
	\begin{tabular}{|>{\centering}p{41mm}|p{106mm}|}
		\hline
		\textbf{Acronym} & \textbf{Expanded Version} \\
		\hline
		}
		{
	\end{tabular}
}



\renewcommand\chapter{\if@openright\cleardoublepage\else\clearpage\fi
  \clearpage
	\thispagestyle{plain}%
	\global\@topnum\z@
	\@afterindentfalse
	\secdef\@chapter\@schapter}
\def\@chapter[#1]#2{\ifnum \c@secnumdepth >\m@ne
	\if@mainmatter
	\refstepcounter{chapter}%
	\typeout{\@chapapp\space\thechapter.}%
	\addcontentsline{toc}{chapter}%
	{\protect\numberline{\thechapter}#1}%
	\else
	\addcontentsline{toc}{chapter}{#1}%
	\fi
	\else
	\addcontentsline{toc}{chapter}{#1}%
	\fi
	\chaptermark{#1}%
	\addtocontents{lof}{\protect\addvspace{10\p@}}%
	\addtocontents{lot}{\protect\addvspace{10\p@}}%
	\if@twocolumn
	\@topnewpage[\@makechapterhead{#2}]%
	\else
	\@makechapterhead{#2}%
	\@afterheading
	\fi}
\def\@makechapterhead#1{%
	\vspace*{50\p@}%
	{\parindent \z@ \raggedright \normalfont
		\ifnum \c@secnumdepth >\m@ne
			\if@mainmatter
			\Huge \bfseries
			\thechapter .  #1\par\nobreak
			\vskip 40\p@
			}}
			\def\@schapter#1{\if@twocolumn
				\@topnewpage[\@makeschapterhead{#1}]%
				\else
				\@makeschapterhead{#1}%
				\@afterheading
				\fi}
			\def\@makeschapterhead#1{%
				\vspace*{50\p@}%
				{\parindent \z@ \raggedright
					\normalfont
					\interlinepenalty\@M
					\Huge \bfseries  #1\par\nobreak
					\vskip 40\p@
			}}
