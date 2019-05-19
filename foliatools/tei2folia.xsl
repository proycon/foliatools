<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
   xmlns:folia="http://ilk.uvt.nl/folia"
   xmlns:edate="http://exslt.org/dates-and-times"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:tei="http://www.tei-c.org/ns/1.0"
   xmlns:xlink="https://www.w3.org/1999/xlink"
   exclude-result-prefixes="tei edate xlink" version="1.0"
   xmlns="http://ilk.uvt.nl/folia"
   xpath-default-namespace="http://www.tei-c.org/ns/1.0">

<!--
TEI2FoLiA Converter

Considering the enormous variety of TEI documents, this converter
only covers a subset and is not guaranteed to work!

Based on work by Jesse de Does (INT)
Heavily adapted by Maarten van Gompel (Radboud University)
-->

<xsl:output method="xml" indent="yes"/>
<!--
  <xsl:strip-space elements="*"/>
-->

<xsl:strip-space elements="l p interp meta interpGrp"/>

<xsl:param name="docid"><xsl:value-of select="//publicationStmt/idno/text()"/></xsl:param>
<xsl:param name='generateIds'>true</xsl:param><!-- We actually rarely do this now -->
<xsl:param name="quiet">false</xsl:param>

<xsl:template name="note-resp">
<xsl:if test="@resp">
<xsl:attribute name="class">resp_<xsl:value-of select="@resp"/></xsl:attribute>
</xsl:if>
</xsl:template>


<xsl:template name="metadata_link"><!-- might be specific for INT collections -->
  <xsl:variable name="inst"><xsl:value-of select="./@xml:id"/></xsl:variable>
  <xsl:if test="//interpGrp[@inst=concat('#',$inst)]">
   <xsl:attribute name="metadata"><xsl:value-of select="./@xml:id"/></xsl:attribute>
  </xsl:if>
</xsl:template>




<!--
 text nodes, inline tags en ignorable tagging binnen t.
  Let op: extra if ook in dergelijke andere templates toevoegen
  Of liever parametriseren
-->

<!-- meer algemeen iets met inline elementen doen wat je hier met hi en name doet -->







<xsl:template match="signed">
<xsl:apply-templates/>
</xsl:template>






<!-- *************************************************** DOCUMENT & METADATA ************************************************** -->

<xsl:template match="TEI|TEI.2">
<FoLiA xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://ilk.uvt.nl/folia" version="2.1.0" generator="tei2folia.xsl">
  <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/></xsl:attribute>
  <metadata type="native">
    <xsl:call-template name="annotations"/>
    <xsl:call-template name="provenance"/>
    <xsl:if test="teiHeader/fileDesc/titleStmt/title">
     <meta id="title"><xsl:value-of select="string(teiHeader/fileDesc/titleStmt/title)" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/fileDesc//editionStmt/edition">
     <meta id="edition"><xsl:value-of select="string(teiHeader/fileDesc//editionStmt/edition)" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/fileDesc//respStmt/resp">
     <meta id="responsibility"><xsl:value-of select="string(teiHeader/fileDesc//respStmt/resp)" /></meta>
    </xsl:if>
    <!-- the following meta fields are probably very DBNL specific -->
    <xsl:if test="teiHeader/fileDesc//publicationStmt/idno[@type='titelcode']">
     <meta id="titelcode"><xsl:value-of select="string(teiHeader/fileDesc//publicationStmt/idno[@type='titelcode'])" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/fileDesc//publicationStmt/idno[@type='format']">
     <meta id="original_format"><xsl:value-of select="string(teiHeader/fileDesc//publicationStmt/idno[@type='format'])" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/fileDesc//publicationStmt/availability">
     <meta id="availability"><xsl:value-of select="string(teiHeader/fileDesc//publicationStmt/availability)" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/fileDesc//notesStmt/note">
     <meta id="note"><xsl:value-of select="string(teiHeader/fileDesc//notesStmt/note)" /></meta>
    </xsl:if>
    <xsl:if test="teiHeader/revisionDesc/change">
     <meta id="note"><xsl:value-of select="string(teiHeader/revisionDesc/change)" /></meta>
    </xsl:if>
    <!-- these we inherited and are INL specific, not sure what it does but we'll leave it in -->
    <xsl:for-each select=".//listBibl[@xml:id='inlMetadata']//interpGrp"><meta id="{./@type}"><xsl:apply-templates mode="meta"/></meta></xsl:for-each>
    <xsl:for-each select=".//listBibl[not(@xml:id='inlMetadata')]">
        <submetadata>
            <xsl:attribute name="xml:id"><xsl:value-of select="substring-after(.//interpGrp/@inst[position()=1],'#')"/></xsl:attribute>
            <xsl:for-each select=".//interpGrp"><meta id="{./@type}"><xsl:apply-templates/></meta></xsl:for-each>
       </submetadata>
    </xsl:for-each>
  </metadata>
  <text>
    <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/>.text</xsl:attribute>
    <xsl:apply-templates select="//text/*" mode="structure"/>
  </text>
</FoLiA>
</xsl:template>

<xsl:template name="annotations">
 <annotations>
     <text-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
     </text-annotation>
<!--
 <entity-annotation annotatortype="auto" set="unknown"/>
-->
  <division-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/divisions.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
  </division-annotation>
  <xsl:if test="//p">
    <paragraph-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/paragraphs.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
    </paragraph-annotation>
  </xsl:if>
  <xsl:if test="//head">
    <head-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/heads.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
    </head-annotation>
  </xsl:if>
  <xsl:if test="//s">
    <sentence-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </sentence-annotation>
  </xsl:if>
  <xsl:if test="//w">
    <token-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </token-annotation>
  </xsl:if>
  <xsl:if test="//list">
      <list-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
      </list-annotation>
  </xsl:if>
  <xsl:if test="//figure">
    <figure-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </figure-annotation>
  </xsl:if>
  <xsl:if test="//table">
    <table-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </table-annotation>
  </xsl:if>
  <xsl:if test="//text//gap|//text//label|//text//note">
   <gap-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/gaps.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </gap-annotation>
   <rawcontent-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
   </rawcontent-annotation>
  </xsl:if>
  <xsl:if test="//text//note">
   <reference-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/references.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </reference-annotation>
  </xsl:if>
  <xsl:if test="//hi">
   <style-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/styles.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </style-annotation>
 </xsl:if>
 <part-annotation annotatortype="auto" set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/parts.foliaset.ttl"> <!-- we use this for parts that the non-XSLT postprocessor processes -->
         <annotator processor="proc.tei2folia.xsl"/>
 </part-annotation>
 <comment-annotation>  <!-- We produce FoLiA comments to report where there were things that couldn't be converted -->
         <annotator processor="proc.tei2folia.xsl"/>
 </comment-annotation>
 <xsl:if test="//w/@pos">
  <pos-annotation set="unknown">
         <annotator processor="proc.tei2folia.xsl"/>
  </pos-annotation>
 </xsl:if>
 <xsl:if test="//w/@lemma">
  <lemma-annotation set="unknown">
         <annotator processor="proc.tei2folia.xsl"/>
  </lemma-annotation>
 </xsl:if>
<xsl:if test="//text//cor|//text//supplied|//text//del">
 <correction-annotation annotatortype="auto" set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/corrections.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </correction-annotation>
</xsl:if>
<xsl:if test="//text//note">
 <note-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/notes.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </note-annotation>
</xsl:if>
 <string-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/strings.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </string-annotation>
<xsl:if test="//sp|//stage">
 <event-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/events.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </event-annotation>
</xsl:if>
<xsl:if test="//lb|//pb">
 <linebreak-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/linebreaks.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </linebreak-annotation>
</xsl:if>
   </annotations>
</xsl:template>

<xsl:template name="provenance">
   <provenance>
    <processor xml:id="proc.tei2folia" name="tei2folia" src="https://github.com/proycon/foliatools">
        <processor xml:id="proc.tei2folia.xsl" name="tei2folia.xsl" />
    </processor>
   </provenance>
</xsl:template>

<xsl:template match="interpGrp/interp" mode="meta"><xsl:variable name="cur"><xsl:value-of select="."/></xsl:variable><xsl:if test="not(../interp[1]=$cur)">|</xsl:if><xsl:apply-templates mode="meta"/></xsl:template>

<xsl:template match="interpGrp/text()" mode="meta"/>

<xsl:template match="interp/text()" mode="meta"><xsl:value-of select="normalize-space(.)"/></xsl:template>

<!-- ************************** HELPER TEMPLATES  *********************** -->

<!-- process underlying text and/or structure-->
<xsl:template name="textandorstructure">
    <xsl:variable name="hasstructure"><xsl:choose><xsl:when test="p|div|s|w|lg|sp|table|row|cell|figure|list|item|cell|speaker|head">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>
    <xsl:variable name="hastext"><xsl:choose><xsl:when test="normalize-space(.) != ''">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>
    <xsl:variable name="hasmarkup"><xsl:choose><xsl:when test="hi|add|name|note|corr|supplied|add|l and normalize-space(string(.)) != ''">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>

    <!--<xsl:comment>DEBUG:<xsl:value-of select="$hasstructure" /><xsl:value-of select="$hastext" /><xsl:value-of select="$hasmarkup" /></xsl:comment>-->

    <xsl:choose>
        <xsl:when test="(number($hasmarkup) = 1 or number($hastext) = 1) and number($hasstructure) = 0">
            <!-- all is text markup, easy -->
            <t><xsl:apply-templates mode="markup" /></t>
        </xsl:when>
        <xsl:when test="number($hasstructure) = 1 and number($hasmarkup) = 0 and number($hastext) = 0">
            <!-- all is structure, easy -->
            <xsl:apply-templates mode="structure" />
        </xsl:when>
        <xsl:otherwise>
            <!-- fall back to structure, this will wrap things in part which can be resolved by a postprocessor -->
            <xsl:apply-templates mode="structure" />
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>


<xsl:template name="p">
    <xsl:text>
    </xsl:text>
    <p>
    <xsl:attribute name="class"><xsl:value-of select="name(.)"/></xsl:attribute>
    <xsl:call-template name="textandorstructure"/>
    </p>
</xsl:template>


<!-- Sentence ID -->
<xsl:template name="setId">
 <xsl:if test="@xml:id or $generateIds='true'">
    <xsl:attribute name="xml:id">
        <xsl:choose>
            <xsl:when test="@ID"><xsl:value-of select="@xml:id"/></xsl:when>
            <xsl:otherwise>e<xsl:number level="any" count="*"/></xsl:otherwise>
        </xsl:choose>
    </xsl:attribute>
 </xsl:if>
</xsl:template>

<!-- ************************** TEMPLATES PRODUCING STRUCTURAL ELEMENTS  *********************** -->

<xsl:template match="front|body|back" mode="structure">
    <div class="{name(.)}matter">
    <xsl:call-template name="haalPbBinnen"/>
    <xsl:apply-templates mode="structure" />
    </div>
</xsl:template>


<xsl:template match="head|docTitle|titlePart[not(ancestor::docTitle)]" mode="structure">
    <xsl:choose>
     <xsl:when test="list|figure|ancestor::item|ancestor::caption">
         <!-- render head as p because of incompatible subelements or super-elements -->
        <p>
        <xsl:attribute name="class">
        <xsl:choose>
            <xsl:when test="@rend"><xsl:value-of select="@rend"/></xsl:when>
            <xsl:otherwise>head</xsl:otherwise>
        </xsl:choose>
        </xsl:attribute>
        <xsl:call-template name="textandorstructure"/>
        </p>
     </xsl:when>
     <xsl:otherwise>
         <!-- normal situation -->
        <head>
        <xsl:attribute name="class">
        <xsl:choose>
            <xsl:when test="@rend"><xsl:value-of select="@rend"/></xsl:when>
            <xsl:otherwise>unspecified</xsl:otherwise>
        </xsl:choose>
        </xsl:attribute>
        <xsl:call-template name="textandorstructure"/>
        </head>
     </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="table" mode="structure">
    <xsl:if test="table/head">
        <!-- move head out of table -->
        <xsl:apply-templates select="table/head" mode="structure" />
    </xsl:if>
    <xsl:choose>
    <xsl:when test="ancestor::cell|ancestor::table|ancestor::item|ancestor::list">
        <!-- nested tables? what are we? HTML in the late nineties? let's just flatten the nested table instead -->
        <comment>[tei2folia WARNING] Nested table occurs here, we flattened it. Results may be unexpected</comment>
        <part class="nestedtable">
        <xsl:for-each select=".//cell/*">
            <xsl:if test="name() != 'table' and name() != 'row' and name() != 'cell'">
             <xsl:apply-templates match="." mode="structure" />
             <br class="cellbreak"/>
            </xsl:if>
        </xsl:for-each>
        </part>
    </xsl:when>
    <xsl:otherwise>
        <!-- normal behaviour -->
        <table>
        <xsl:apply-templates mode="structure" />
        </table>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="cell" mode="structure">
    <cell>
        <xsl:call-template name="textandorstructure"/>
    </cell>
</xsl:template>

<xsl:template match="p|speaker|trailer|closer|opener|lxx" mode="structure">
    <xsl:call-template name="p"/>
</xsl:template>

<!-- we can't have tables, figures or lists inside paragraphs -->
<xsl:template match="p[./table|./figure|./list]|xcloser[./list]|xcloser[./signed/list]" mode="structure">
    <!-- just forget about the P and handle everything inside directly: -->
    <xsl:apply-templates mode="structure" />
</xsl:template>

<!-- we can't have breaks in lists or table (rows)-->
<xsl:template match="table/pb|list/pb|row/pb|figure/pb" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message>WARNING: Skipped over pagebreak in table/list/row/figure</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Skipped over pagebreak here</comment>
</xsl:template>

<xsl:template match="figure" mode="structure">
    <xsl:if test="figure/head">
        <!-- move head out of figure -->
        <xsl:apply-templates select="figure/head" mode="structure" />
    </xsl:if>
    <xsl:choose>
    <xsl:when test="ancestor::list|ancestor::quote|ancestor::q">
        <xsl:if test="$quiet = 'false'">
        <xsl:message>WARNING: Skipped over figure in list/quote</xsl:message>
        </xsl:if>
        <comment>[tei2folia WARNING] Skipped over figure in list/quote</comment>
    </xsl:when>
    <xsl:otherwise>
        <!-- normal behaviour -->
    <figure>
        <xsl:if test="xptr">
        <xsl:attribute name="src"><xsl:value-of select="xptr/@to" /></xsl:attribute>
        </xsl:if>
        <xsl:apply-templates select="figDesc" mode="structure"/>
    </figure>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="figDesc" mode="structure">
    <caption>
    <xsl:call-template name="textandorstructure"/>
    </caption>
</xsl:template>

<xsl:template match="list" mode="structure">
    <xsl:if test="list/head">
        <!-- move head out of list -->
        <xsl:apply-templates select="table/list" mode="structure" />
    </xsl:if>
    <list>
        <xsl:apply-templates mode="structure"/>
    </list>
</xsl:template>

<!-- Handles both tei:item and preceding tei:label, in list context -->
<xsl:template match="item" mode="structure">
     <xsl:choose>
      <xsl:when test="name(preceding-sibling::*[1]) = 'label'">
        <item>
        <xsl:attribute name="n"><xsl:value-of select="string(preceding-sibling::*[1])" /></xsl:attribute>
        <xsl:choose>
        <xsl:when test="list|table|p|s|w">
        <gap class="label">
        <content><xsl:value-of select="string(preceding-sibling::*[1])" /></content>
        </gap>
        <xsl:apply-templates mode="structure" />
        </xsl:when>
        <xsl:otherwise>
        <t><t-gap class="label"><xsl:value-of select="string(preceding-sibling::*[1])" /></t-gap><xsl:text> </xsl:text> <xsl:apply-templates mode="markup"/></t>
        </xsl:otherwise>
        </xsl:choose>
        </item>
      </xsl:when>
      <xsl:otherwise>
        <item>
        <xsl:call-template name="textandorstructure" />
        </item>
     </xsl:otherwise>
</xsl:choose>
</xsl:template>



<xsl:template match="lg" mode="structure">
    <xsl:text>
    </xsl:text>
    <xsl:choose>
    <xsl:when test="ancestor::figDesc|ancestor::item">
        <!-- no divisions allowed under captions, just descend into substructures -->
        <xsl:apply-templates mode="structure" />
    </xsl:when>
    <xsl:otherwise>
        <div>
        <xsl:attribute name="class"><xsl:choose><xsl:when test="@type"><xsl:value-of select="@type" /></xsl:when><xsl:otherwise>linegroup</xsl:otherwise></xsl:choose></xsl:attribute>
        <xsl:call-template name="textandorstructure" />
        </div>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="epigraph" mode="structure">
    <div class="epigraph">
    <xsl:call-template name="textandorstructure" />
    </div>
</xsl:template>

<xsl:template match="row" mode="structure">
    <row>
    <xsl:apply-templates mode="structure" />
    </row>
</xsl:template>

<xsl:template match="div|div0|div1|div2|div3|div4|div5|div6|div7|titlePage|argument" mode="structure">
 <xsl:element name="div">
    <xsl:attribute name="class"><xsl:choose><xsl:when test="@type"><xsl:value-of select="@type" /></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute>
    <xsl:call-template name="metadata_link"/><!-- for INT collections? -->
    <xsl:apply-templates mode="structure" />
 </xsl:element>
</xsl:template>

<xsl:template match="q|quote" mode="structure">
    <xsl:choose>
      <xsl:when test="list|table">
         <!-- having quotes here makes no sense, just process children as structure -->
        <xsl:apply-templates mode="structure" />
      </xsl:when>
      <xsl:otherwise>
         <!-- normal behaviour -->
        <quote>
        <xsl:call-template name="textandorstructure" />
        </quote>
      </xsl:otherwise>
     </xsl:choose>
</xsl:template>


<xsl:template match="gap" mode="structure">
    <gap annotator="{@resp}" class="{@reason}"/>
</xsl:template>

<xsl:template match="interpGrp" mode="structure">
<comment>
<xsl:for-each select="./interp">
    interp[<xsl:value-of select="@type"/>]: <xsl:value-of select="@value" />
</xsl:for-each>
</comment>
</xsl:template>

<!-- Valid both as structural and as markup, easy -->
<xsl:template match="lb" mode="structure"><xsl:call-template name="lb" /></xsl:template>
<xsl:template match="cb" mode="structure"><xsl:call-template name="cb" /></xsl:template>
<xsl:template match="pb" mode="structure"><xsl:call-template name="pb" /></xsl:template>


<!-- Markup elements in structural mode, wrap in part (to be sorted by postprocessor later)-->


<!-- Text structural mode, wrap in part (to be sorted by postprocessor later!)-->
<xsl:template match="l" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-l"><t><xsl:call-template name="l" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="hi" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-hi"><t><xsl:call-template name="hi" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="add" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-add"><t><xsl:call-template name="add" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="corr" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-corr"><t><xsl:call-template name="corr" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="supplied" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-supplied"><t><xsl:call-template name="supplied" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="del" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-del"><t><xsl:call-template name="del" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="note" mode="structure">
    <xsl:if test="normalize-space(string(.))">
    <part class="temp-note"><t><xsl:call-template name="note" /></t></part> <!-- this deliberately does not resolve to notes yet, our postprocessor creates the notes -->
    </xsl:if>
</xsl:template>

<xsl:template match="text()" mode="structure">
<xsl:if test="normalize-space(.)">
<part class="temp-text"><t><xsl:value-of select="." /></t></part>
</xsl:if>
</xsl:template>

<xsl:template match="title" mode="structure">
<xsl:if test="normalize-space(string(.))">
<part class="temp-title"><t><xsl:call-template name="title" /></t></part>
</xsl:if>
</xsl:template>

<xsl:template match="name" mode="structure">
<xsl:if test="normalize-space(string(.))">
<part class="temp-name"><t><xsl:call-template name="name" /></t></part>
</xsl:if>
</xsl:template>

<!-- ************************** TEMPLATES PRODUCING MARKUP ELEMENTS  *********************** -->

<!-- These come in name/match template pairs as they are also referenced by the structural variants -->

<xsl:template name="name">
<xsl:if test="normalize-space(string(.))">
<t-str class="name">
<xsl:choose>
<xsl:when test="@type">
<xsl:attribute name="class"><xsl:value-of select="@type"/>-name</xsl:attribute>
</xsl:when>
<xsl:otherwise>
<xsl:attribute name="class">name</xsl:attribute>
</xsl:otherwise>
</xsl:choose>
<xsl:apply-templates mode="markup"/>
</t-str>
</xsl:if>
</xsl:template>

<xsl:template match="name" mode="markup">
<xsl:call-template name="name" />
</xsl:template>



<xsl:template name="add">
<t-str class="addition">
<xsl:apply-templates mode="markup" />
</t-str>
</xsl:template>

<xsl:template match="add" mode="markup">
<xsl:call-template name="add" />
</xsl:template>

<!-- styling (tei:hi) -->
<xsl:template name="hi">
<xsl:if test="normalize-space(string(.))">
<t-style><xsl:attribute name="class"><xsl:choose><xsl:when test="@rendition"><xsl:value-of select="@rendition"/></xsl:when><xsl:when test="@rend"><xsl:value-of select="@rend"/></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute><xsl:apply-templates mode="markup"/></t-style>
</xsl:if>
</xsl:template>

<xsl:template match="hi" mode="markup">
<xsl:call-template name="hi" />
</xsl:template>


<!-- Valid both as structural and as markup, easy -->
<xsl:template name="lb"><br class="linebreak"/></xsl:template>
<xsl:template name="cb"><br class="columnbreak"/></xsl:template>
<xsl:template name="pb"><br class="pagebreak" newpage="yes" pagenr="{@n}"/></xsl:template>

<xsl:template match="lb" mode="markup"><xsl:call-template name="lb" /></xsl:template>
<xsl:template match="cb" mode="markup"><xsl:call-template name="cb" /></xsl:template>
<xsl:template match="pb" mode="markup"><xsl:call-template name="pb" /></xsl:template>


<!-- Corrections -->
<!-- TODO: annotators should be in provenance chain, specifying them here probably fails even now -->
<xsl:template name="corr"><t-correction class="correction" annotator="{@resp}" original="{@sic}"><xsl:apply-templates mode="markup"/></t-correction></xsl:template>

<xsl:template name="supplied"><t-correction class="supplied" annotator="{@resp}"><xsl:apply-templates mode="markup"/></t-correction></xsl:template>

<xsl:template name="del"><t-correction class="deletion" annotator="{@resp}" original="{.//text()}"></t-correction></xsl:template>

<xsl:template match="corr" mode="markup"><xsl:call-template name="corr" /></xsl:template>
<xsl:template match="supplied" mode="markup"><xsl:call-template name="supplied" /></xsl:template>
<xsl:template match="del" mode="markup"><xsl:call-template name="del" /></xsl:template>

<!-- Notes -->
<xsl:template name="note">
        <t-ref><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if>
        <xsl:choose>
        <xsl:when test="@type">
        <xsl:attribute name="class">note-<xsl:value-of select="@type" /></xsl:attribute>
        </xsl:when>
        <xsl:when test="@place = 'foot'">
        <xsl:attribute name="class">footnote</xsl:attribute>
        </xsl:when>
        <xsl:otherwise>unspecified</xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates mode="markup" /></t-ref>
</xsl:template>

<xsl:template match="note" mode="markup"><xsl:call-template name="note" /></xsl:template>

<xsl:template name="quote">
    <xsl:if test="normalize-space(string(.))">
    <t-str class="quote"><xsl:apply-templates mode="markup" /></t-str>
    </xsl:if>
</xsl:template>
<xsl:template match="q|quote" mode="markup"><xsl:call-template name="quote" /></xsl:template>

<xsl:template name="gap">
    <t-gap annotator="{@resp}" class="{@reason}"/>
</xsl:template>
<xsl:template match="gap" mode="markup"><xsl:call-template name="gap" /></xsl:template>

<xsl:template match="note[./table|./figure|./list|./p]" mode="markup">
<xsl:if test="$quiet = 'false'">
<xsl:message>WARNING: There is a table, list or figure or paragraph in a note, the converter can't handle this currently</xsl:message>
</xsl:if>
<t-gap class="unprocessable-note" n="{@n}"/>
</xsl:template>


<xsl:template name="l">
<xsl:if test="normalize-space(string(.))">
<t-str class="l"><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:apply-templates mode="markup"/></t-str><br class='poetic.linebreak'><xsl:if test="@n"><xsl:attribute name="n"><xsl:value-of select="@n" /></xsl:attribute></xsl:if></br>
</xsl:if>
</xsl:template>

<xsl:template match="l" mode="markup">
<xsl:call-template name="l" />
</xsl:template>

<!-- default text node behaviour -->
<xsl:template match="text()" mode="markup">
<xsl:value-of select="." />
</xsl:template>

<xsl:template name="title">
<xsl:if test="normalize-space(string(.))">
<t-str class="title"><xsl:apply-templates mode="markup" /></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="title" mode="markup">
<xsl:call-template name="title" />
</xsl:template>

<!-- ************************** TEMPLATES DELETING ELEMENTS  *********************** -->

<!-- Deletion often occurs because the element is already handled elsewhere -->

<!-- I suppose this cleans up something from some preprocessing step? leaving it in just in case -->
<xsl:template match="supplied[./text()='leeg']" mode="markup"/>
<xsl:template match="supplied[./text()='leeg']" mode="structure"/>

<!-- Handled by item -->
<xsl:template match="label" mode="structure"/>

<!-- Handled by table -->
<xsl:template match="table/head" mode="structure"/>

<!-- Handled by list -->
<xsl:template match="list/head" mode="structure"/>

<!-- Handled by figure -->
<xsl:template match="figure/head" mode="structure"/>

<!-- *********************************** PAGEBREAK MAGIC **************************************************** -->

<xsl:template match="text/pb|table/pb|row/pb|list/pb" mode="structure"><comment>Skipping pagebreak here</comment></xsl:template>
<xsl:template match="list/lb|row/lb|table/lb" mode="structure"><comment>Skipping linebreak here</comment></xsl:template>
<xsl:template match="text/pb|table/pb|row/pb|list/pb" mode="markup"><comment>Skipping pagebreak here</comment></xsl:template>
<xsl:template match="list/lb|row/lb|table/lb" mode="markup"><comment>Skipping linebreak here</comment></xsl:template>

<!-- I'm not entirely sure what this does but it looks well thought out (proycon) -->

<!--
<xsl:template match="pb|div//pb|div1//pb|div2//pb|div3//pb|titlePage//pb|p//pb|trailer//pb|closer//pb">
<xsl:call-template name="pb"/>
</xsl:template>

<xsl:template match="pb/maarnietechthoor">
<xsl:if test="not (ancestor::div or ancestor::div1 or ancestor::titlePage or ancestor::p) and (following-sibling::*[1][self::div or self::div1 or self::div2 or self::div3 or self::titlePage])">
<xsl:comment>verplaatste pagebreak</xsl:comment>
</xsl:if>
<xsl:if test="ancestor::div or ancestor::titlePage or ancestor::div1">
<xsl:comment>legale pagebreak</xsl:comment>
</xsl:if>
<xsl:if test="not (ancestor::div or ancestor::div1 or ancestor::titlePage or ancestor::pb) and not(following-sibling::*[1][self::div or self::div1 or self::div2 or self::div3 or self::titlePage])">
<xsl:comment>verloren pagebreak</xsl:comment>
</xsl:if>
</xsl:template>
-->

<xsl:template name="haalPbBinnen">
<xsl:for-each select="preceding-sibling::*[1]">
<xsl:if test="self::pb and (not(ancestor::div)) and (not(ancestor::div1))  and (not(ancestor::titlePage))">
<comment>opgeviste pagebreak:</comment>
<xsl:call-template name="pb"/>
</xsl:if>
</xsl:for-each>
</xsl:template>



<xsl:template name="haalPbBinnenInCel">
<xsl:for-each select="..">
<xsl:for-each select="preceding-sibling::*[1]">
<xsl:if test="self::pb">
<comment>opgeviste pagebreak naar cel</comment>
<xsl:call-template name="pb"/>
</xsl:if>
</xsl:for-each>
</xsl:for-each>
</xsl:template>


<!-- ********************************* CRUFT ****************************************************** -->



<!-- disabled XSLT 2.0 (proycon)
<xsl:template match="p[./table|./figure|./list]|xcloser[./list]|xcloser[./signed/list]">
<xsl:for-each-group select="node()" group-ending-with="table">
<p>
<t><xsl:apply-templates select="current-group()[not(self::table or self::figure or self::list or self::signed)]"/></t>
</p>
<xsl:apply-templates select="current-group()[self::table or self::figure or self::list or self::signed]"/>
</xsl:for-each-group>
</xsl:template>
-->



<!-- disabled because of XSLT2.0 (proycon)
<xsl:template match="hi[./lb]">
<xsl:variable name="class"><xsl:value-of select="@rendition"/><xsl:value-of select="@rend"/></xsl:variable>
<xsl:for-each-group select="node()" group-ending-with="lb">
<t-style class="{$class}">
<xsl:apply-templates select="current-group()[not(self::lb)]"/>
</t-style>
<xsl:apply-templates select="current-group()[self::lb]"/>
</xsl:for-each-group>
</xsl:template>
-->




<xsl:template match="delSpan">
<xsl:variable name="spanTo"><xsl:value-of select="@spanTo"/></xsl:variable>
<xsl:variable name="end"><xsl:value-of select="following-sibling::anchor[@xml:id=$spanTo]"/></xsl:variable>
<xsl:if test="$end">
<xsl:message>Deleted text: (<xsl:value-of select="name($end)"/>) <xsl:value-of select="$end/preceding-sibling::node()[preceding-sibling::delSpan[@spanTo=$spanTo]]"/>
</xsl:message>
</xsl:if>
</xsl:template>


<xsl:template match="sp" mode="structure">
    <xsl:choose>
    <xsl:when test="ancestor::figDesc|ancestor::item|ancestor::quote|ancestor::q">
        <!-- no events allowed under these elements, just descend into substructures -->
        <xsl:apply-templates mode="structure" />
    </xsl:when>
    <xsl:otherwise>
        <!-- normal behaviour -->
        <event class="speakerturn">
        <xsl:choose>
        <xsl:when test=".//speaker/hi">
            <xsl:attribute name="actor"><xsl:value-of select="string(.//speaker/hi)" /></xsl:attribute>
        </xsl:when>
        <xsl:when test=".//speaker">
            <xsl:attribute name="actor"><xsl:value-of select="string(.//speaker)" /></xsl:attribute>
        </xsl:when>
        </xsl:choose>
        <xsl:call-template name="textandorstructure" />
        </event>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="stage" mode="structure">
<event class="stage">
    <xsl:call-template name="textandorstructure"/>
</event>
</xsl:template>



<xsl:template match="add[@resp='transcriber']"/>



<!-- ********************************** WARNINGS ***************************************************** -->

<xsl:template match="item/figure" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in item! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in item! (not allowed)</comment>
</xsl:template>

<xsl:template match="quote/figure|q/figure" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in quote! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in quote! (not allowed)</comment>
</xsl:template>

<xsl:template match="figDesc/figure|figDesc/list|figDesc/table" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in caption! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in caption! (not allowed)</comment>
</xsl:template>


<!-- generic fallbacks -->

<xsl:template match="*" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag in structure context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Unhandled tag in structure context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</comment>
</xsl:template>

<xsl:template match="*" mode="markup">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag in markup context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Unhandled tag in markup context: tei:<xsl:value-of select="name(.)"/> (in tei:<xsl:value-of select="name(parent::node())" />)</comment>
</xsl:template>

<xsl:template match="*">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Unhandled tag: tei:<xsl:value-of select="name(.)"/> (in tei:<xsl:value-of select="name(parent::node())" />)</comment>
</xsl:template>


</xsl:stylesheet>
