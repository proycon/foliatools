<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
   xmlns:folia="http://ilk.uvt.nl/folia"
   xmlns:edate="http://exslt.org/dates-and-times"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:tei="http://www.tei-c.org/ns/1.0"
   xmlns:xlink="http://www.w3.org/1999/xlink"
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

<xsl:strip-space elements="tei:l tei:p tei:interp tei:meta tei:interpGrp"/>

<xsl:param name="docid"><xsl:choose><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='DOI']/text())">DOI.<xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='DOI']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='ISSN']/text())">ISSN.<xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='ISSN']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='ISBN']/text())">ISBN.<xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='ISBN']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='DTADirName']/text())"><xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno/tei:idno[@type='DTADirName']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno[@type='WV_ID']/text())"><xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno[@type='WV_ID']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno[@type='ID']/text())"><xsl:value-of select="normalize-space(//tei:publicationStmt/tei:idno[@type='ID']/text())" /></xsl:when><xsl:when test="normalize-space(//tei:publicationStmt/tei:idno/text())"><xsl:value-of select="translate(translate(translate(translate(normalize-space(//tei:publicationStmt/tei:idno/text()),'/','_'), ':','_'),'#','_'),'@','_')"/></xsl:when><xsl:otherwise>undefined</xsl:otherwise></xsl:choose></xsl:param>
<xsl:param name='generateIds'>false</xsl:param>  <!-- better leave this up to postprocessing tools (e.g. foliaid) -->
<xsl:param name="quiet">false</xsl:param>

<xsl:key name="correctors" match="//tei:corr|//tei:supplied|//tei:del" use="@resp" />

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






<xsl:template match="tei:signed">
<xsl:apply-templates/>
</xsl:template>






<!-- *************************************************** DOCUMENT & METADATA ************************************************** -->

<xsl:template match="TEI|TEI.2">
    <xsl:message terminate="yes">ERROR: TEI document lacks proper XML namespace declarations! Run tei2folia --forcenamespace to try to recover automatically or add xmlns="http://www.tei-c.org/ns/1.0" manually.</xsl:message>
</xsl:template>

<xsl:template match="tei:TEI|tei:TEI.2">
<FoLiA xmlns:xlink="http://www.w3.org/1999/xlink" xmlns="http://ilk.uvt.nl/folia" version="2.3.0" generator="tei2folia.xsl">
  <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/></xsl:attribute>
  <metadata type="native">
    <xsl:call-template name="annotations"/>
    <xsl:call-template name="provenance"/>
    <xsl:if test="tei:TeiHeader/tei:fileDesc/tei:titleStmt/tei:title">
     <meta id="title"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc/tei:titleStmt/tei:title)" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:editionStmt/edition">
     <meta id="edition"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:editionStmt/tei:edition)" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:respStmt/resp">
     <meta id="responsibility"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:respStmt/tei:resp)" /></meta>
    </xsl:if>
    <!-- the following meta fields are probably very DBNL specific -->
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:idno[@type='titelcode']">
     <meta id="titelcode"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:idno[@type='titelcode'])" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:idno[@type='format']">
     <meta id="original_format"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:idno[@type='format'])" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:availability">
     <meta id="availability"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:publicationStmt/tei:availability)" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:fileDesc//tei:notesStmt/tei:note">
     <meta id="note"><xsl:value-of select="string(tei:TeiHeader/tei:fileDesc//tei:notesStmt/tei:note)" /></meta>
    </xsl:if>
    <xsl:if test="tei:TeiHeader/tei:revisionDesc/tei:change">
     <meta id="note"><xsl:value-of select="string(tei:TeiHeader/tei:revisionDesc/tei:change)" /></meta>
    </xsl:if>
    <!-- these we inherited and are INL specific, not sure what it does but we'll leave it in -->
    <xsl:for-each select=".//tei:listBibl[@xml:id='inlMetadata']//tei:interpGrp"><meta id="{./@type}"><xsl:apply-templates mode="meta"/></meta></xsl:for-each>
    <xsl:for-each select=".//tei:listBibl[not(@xml:id='inlMetadata')]">
        <submetadata>
            <xsl:attribute name="xml:id"><xsl:value-of select="substring-after(.//tei:interpGrp/@inst[position()=1],'#')"/></xsl:attribute>
            <xsl:for-each select=".//tei:interpGrp"><meta id="{./@type}"><xsl:apply-templates/></meta></xsl:for-each>
       </submetadata>
    </xsl:for-each>
  </metadata>
  <text>
    <xsl:attribute name="xml:id"><xsl:value-of select="$docid"/>.text</xsl:attribute>
    <xsl:apply-templates select="//tei:text/*" mode="structure"/>
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
  <xsl:if test="//tei:p">
    <paragraph-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/paragraphs.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
    </paragraph-annotation>
  </xsl:if>
  <xsl:if test="//tei:head">
    <head-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/heads.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
    </head-annotation>
  </xsl:if>
  <xsl:if test="//tei:s">
    <sentence-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </sentence-annotation>
  </xsl:if>
  <xsl:if test="//tei:w">
    <token-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </token-annotation>
  </xsl:if>
  <xsl:if test="//tei:list">
      <list-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
      </list-annotation>
  </xsl:if>
  <xsl:if test="//tei:figure">
    <figure-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </figure-annotation>
  </xsl:if>
  <xsl:if test="//tei:table">
    <table-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
    </table-annotation>
  </xsl:if>
  <xsl:if test="//tei:text//tei:gap|//tei:text//tei:label|//tei:text//tei:note">
   <gap-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/gaps.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </gap-annotation>
   <rawcontent-annotation>
         <annotator processor="proc.tei2folia.xsl"/>
   </rawcontent-annotation>
  </xsl:if>
  <xsl:if test="//tei:text//tei:note">
   <reference-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/references.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </reference-annotation>
  </xsl:if>
  <xsl:if test="//tei:hi">
   <style-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/styles.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
   </style-annotation>
 </xsl:if>
 <part-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/parts.foliaset.ttl"> <!-- we use this for parts that the non-XSLT postprocessor processes -->
         <annotator processor="proc.tei2folia.xsl"/>
 </part-annotation>
 <comment-annotation>  <!-- We produce FoLiA comments to report where there were things that couldn't be converted -->
         <annotator processor="proc.tei2folia.xsl"/>
 </comment-annotation>
 <xsl:if test="//tei:w/@pos">
  <pos-annotation set="unknown">
         <annotator processor="proc.tei2folia.xsl"/>
  </pos-annotation>
 </xsl:if>
 <xsl:if test="//tei:w/@lemma">
  <lemma-annotation set="unknown">
         <annotator processor="proc.tei2folia.xsl"/>
  </lemma-annotation>
 </xsl:if>
 <xsl:if test="//tei:w/@lemmaref|//pb/@facs">
  <relation-annotation set="unknown">
         <annotator processor="proc.tei2folia.xsl"/>
  </relation-annotation>
 </xsl:if>
<xsl:if test="//tei:text//tei:cor|//tei:text//tei:supplied|//tei:text//tei:del">
 <correction-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/corrections.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
         <xsl:for-each select="//tei:*[(contains(name(), 'corr') or contains(name(), 'del') or contains(name(), 'supplied')) and generate-id() = generate-id(key('correctors', @resp)[1])]">
             <xsl:if test="@resp">
                 <annotator>
                     <xsl:attribute name="processor">proc.corrector.<xsl:value-of select="translate(@resp, ' :&#160;', '')" /></xsl:attribute>
                 </annotator>
             </xsl:if>
         </xsl:for-each>
 </correction-annotation>
</xsl:if>
<xsl:if test="//tei:text//tei:note">
 <note-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/notes.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </note-annotation>
</xsl:if>
 <string-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/strings.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </string-annotation>
<xsl:if test="//tei:sp|//tei:stage">
 <event-annotation set="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/events.foliaset.ttl">
         <annotator processor="proc.tei2folia.xsl"/>
 </event-annotation>
</xsl:if>
<xsl:if test="//tei:lb|//tei:pb|//tei:l">
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
        <xsl:for-each select="//tei:*[(contains(name(), 'corr') or contains(name(), 'del') or contains(name(), 'supplied')) and generate-id() = generate-id(key('correctors', @resp)[1])]">
             <xsl:if test="@resp">
                 <processor name="{@resp}">
                     <xsl:attribute name="xml:id">proc.corrector.<xsl:value-of select="translate(@resp, ' :&#160;', '')" /></xsl:attribute>
                 </processor>
             </xsl:if>
         </xsl:for-each>
    </processor>
   </provenance>
</xsl:template>



<xsl:template match="tei:interpGrp/tei:interp" mode="meta"><xsl:variable name="cur"><xsl:value-of select="."/></xsl:variable><xsl:if test="not(../tei:interp[1]=$cur)"><xsl:text>; </xsl:text></xsl:if><xsl:apply-templates mode="meta"/></xsl:template>

<xsl:template match="tei:interpGrp/text()" mode="meta"/>

<xsl:template match="tei:interp/text()" mode="meta"><xsl:value-of select="normalize-space(.)"/></xsl:template>

<!-- ************************** HELPER TEMPLATES  *********************** -->

<!-- process underlying text and/or structure-->
<xsl:template name="textandorstructure">
    <xsl:variable name="hastext"><xsl:choose><xsl:when test="normalize-space(translate(., '&#160;', ' ')) != ''">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>
    <xsl:variable name="hasmarkup"><xsl:choose><xsl:when test="tei:hi|tei:add|tei:name|tei:note|tei:corr|tei:supplied|tei:add|tei:l and number($hastext) = 1">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>
    <xsl:variable name="hasstructure"><xsl:choose><xsl:when test="tei:p|tei:div|tei:s|tei:w|tei:fw|tei:pc|tei:lg|tei:sp|tei:table|tei:row|tei:cell|tei:figure|tei:list|tei:item|tei:cell|tei:speaker|tei:head">1</xsl:when><xsl:when test="number($hasmarkup = 1) and .//tei:w[1]|.//tei:s[1]|.//tei:p[1]">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>

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
    <xsl:call-template name="setId" />
    <xsl:attribute name="class"><xsl:value-of select="name(.)"/></xsl:attribute>
    <xsl:call-template name="textandorstructure"/>
    </p>
</xsl:template>

<xsl:template name="s">
    <xsl:text>
    </xsl:text>
    <s>
        <xsl:call-template name="setId" />
        <xsl:call-template name="textandorstructure"/>
    </s>
</xsl:template>

<xsl:template name="w">
    <xsl:variable name="hastext"><xsl:choose><xsl:when test="normalize-space(translate(., '&#160;', ' ')) != ''">1</xsl:when><xsl:otherwise>0</xsl:otherwise></xsl:choose></xsl:variable>
    <xsl:choose>
    <xsl:when test="parent::tei:table|parent::tei:list|parent::tei:table|parent::tei:row">
        <!-- sanity check to prevent invalid FoLiA -->
        <xsl:if test="$quiet = 'false'">
            <xsl:message terminate="no">WARNING: Rendering a word directly in list/figure/table/row context is invalid! Word will be ignored!</xsl:message>
        </xsl:if>
        <comment>[tei2folia WARNING] Rendering a word directly in this context is invalid! Word was ignored!</comment>
    </xsl:when>
    <xsl:when test="number($hastext) = 1">
    <xsl:text>
    </xsl:text>
    <w>
        <xsl:call-template name="setId" />
        <xsl:attribute name="class"><xsl:value-of select="name(.)"/><xsl:if test="@type">.<xsl:value-of select="@type"/></xsl:if></xsl:attribute> <!-- class can be w, pc, optionally with type like pc.interrogative -->
        <xsl:if test="@join='right' or @join='both'"><xsl:attribute name="space">no</xsl:attribute></xsl:if>
        <t><xsl:apply-templates mode="markup" /></t>
        <xsl:if test="normalize-space(translate(@norm, '&#160;',' ')) != ''">
        <t class="norm"><xsl:value-of select="@norm"/></t>
        </xsl:if>
        <!-- process inline annotations -->
        <xsl:if test="normalize-space(@pos) != ''">
            <pos>
                <xsl:attribute name="class"><xsl:value-of select="normalize-space(@pos)" /></xsl:attribute>
                <xsl:if test="normalize-space(@msd) != ''">
                    <feat subset="msd"><xsl:attribute name="class"><xsl:value-of select="@msd" /></xsl:attribute></feat>
                </xsl:if>
            </pos>
        </xsl:if>
        <xsl:if test="normalize-space(@lemma) != ''">
            <lemma>
                <xsl:attribute name="class"><xsl:value-of select="normalize-space(@lemma)" /></xsl:attribute>
                <xsl:if test="@lemmaRef">
                    <relation class="lemmaref" xlink:type="simple" xlink:href="{@lemmaRef}"/>
                </xsl:if>
            </lemma>
        </xsl:if>
    </w>
    </xsl:when>
    <xsl:otherwise>
        <xsl:if test="$quiet = 'false'">
            <xsl:message terminate="no">WARNING: Skipped a word with no text</xsl:message>
        </xsl:if>
        <comment>[tei2folia WARNING] Skipped a word with no text</comment>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>


<xsl:template name="setId">
 <xsl:if test="@xml:id or $generateIds='true'">
    <xsl:attribute name="xml:id">
        <xsl:choose>
            <xsl:when test="@xml:id"><xsl:value-of select="@xml:id"/></xsl:when>
            <xsl:otherwise>e<xsl:number level="any" count="*"/></xsl:otherwise>
        </xsl:choose>
    </xsl:attribute>
 </xsl:if>
</xsl:template>

<!-- ************************** TEMPLATES PRODUCING STRUCTURAL ELEMENTS  *********************** -->

<xsl:template match="tei:front|tei:body|tei:back" mode="structure">
    <div class="{name(.)}matter">
    <xsl:call-template name="haalPbBinnen"/>
    <xsl:apply-templates mode="structure" />
    </div>
</xsl:template>

<xsl:template match="tei:head|tei:docTitle|tei:titlePart[not(ancestor::tei:docTitle)]|tei:docAuthor|tei:docImprint" mode="structure">
    <xsl:choose>
     <xsl:when test="ancestor::tei:list|ancestor::tei:figure|ancestor::tei:item|ancestor::tei:figDesc">
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
            <xsl:when test="local-name(.) = 'docAuthor'">author</xsl:when>
            <xsl:when test="local-name(.) = 'docImprint'">imprint</xsl:when>
            <xsl:when test="local-name(.) = 'docDate'">date</xsl:when>
            <xsl:otherwise>unspecified</xsl:otherwise>
        </xsl:choose>
        </xsl:attribute>
        <xsl:call-template name="textandorstructure"/>
        </head>
     </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="tei:table" mode="structure">
    <xsl:if test="./tei:head">
        <!-- move head out of table -->
        <xsl:apply-templates select="./tei:head" mode="structure" />
    </xsl:if>
    <xsl:choose>
    <xsl:when test="ancestor::tei:cell|ancestor::tei:table|ancestor::tei:item|ancestor::tei:list|ancestor::tei:quote|ancestor::tei:q">
        <!-- nested tables? what are we? HTML in the late nineties? let's just flatten the nested table instead -->
        <comment>[tei2folia WARNING] Nested table (or table in invalid context) occurs here, we flattened it. Results may be unexpected</comment>
        <part class="nestedtable">
        <xsl:for-each select=".//tei:cell/*">
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
        <xsl:apply-templates select="*[local-name() != 'trailer']" mode="structure"/>
        </table>
    </xsl:otherwise>
    </xsl:choose>
    <xsl:if test="./tei:trailer">
        <!-- move head out of figure -->
        <xsl:apply-templates select="./tei:trailer" mode="structure" />
    </xsl:if>
</xsl:template>

<xsl:template match="tei:cell" mode="structure">
    <cell>
        <xsl:call-template name="textandorstructure"/>
    </cell>
</xsl:template>

<xsl:template match="tei:p|tei:speaker|tei:trailer|tei:closer|tei:opener|tei:lxx|tei:byline|tei:salute" mode="structure">
    <xsl:call-template name="p"/>
</xsl:template>

<xsl:template match="tei:s" mode="structure">
    <xsl:call-template name="s"/>
</xsl:template>

<xsl:template match="tei:w|tei:fw|tei:pc" mode="structure">
    <xsl:call-template name="w"/>
</xsl:template>

<!-- we can't have tables, figures or lists inside paragraphs -->
<xsl:template match="tei:p[./tei:table|./tei:figure|./tei:list]|tei:xcloser[./tei:list]|tei:xcloser[./tei:signed/tei:list]" mode="structure">
    <!-- just forget about the P and handle everything inside directly: -->
    <xsl:apply-templates mode="structure" />
</xsl:template>

<xsl:template match="tei:figure" mode="structure">
    <xsl:if test="./tei:head">
        <!-- move head out of figure -->
        <xsl:apply-templates select="./tei:head" mode="structure" />
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
        <xsl:if test="tei:xptr">
        <xsl:attribute name="src"><xsl:value-of select="tei:xptr/@to" /></xsl:attribute>
        </xsl:if>
        <xsl:apply-templates select="tei:figDesc" mode="structure"/>
    </figure>
    </xsl:otherwise>
    </xsl:choose>
    <xsl:if test="./tei:trailer">
        <!-- move head out of figure -->
        <xsl:apply-templates select="./tei:trailer" mode="structure" />
    </xsl:if>
</xsl:template>

<xsl:template match="tei:figDesc" mode="structure">
    <caption>
    <xsl:call-template name="textandorstructure"/>
    </caption>
</xsl:template>

<xsl:template match="tei:list" mode="structure">
    <xsl:if test="./tei:head">
        <!-- move head out of list -->
        <xsl:apply-templates select="./tei:head" mode="structure" />
    </xsl:if>
    <list>
        <xsl:apply-templates select="*[local-name() != 'trailer']" mode="structure"/>
    </list>
    <xsl:if test="./tei:trailer">
        <!-- move head out of list -->
        <xsl:apply-templates select="./tei:trailer" mode="structure" />
    </xsl:if>
</xsl:template>

<!-- Handles both tei:item and preceding tei:label, in list context -->
<xsl:template match="tei:item" mode="structure">
     <xsl:choose>
      <xsl:when test="name(preceding-sibling::*[1]) = 'label'">
        <item>
        <xsl:attribute name="n"><xsl:value-of select="string(preceding-sibling::*[1])" /></xsl:attribute>
        <xsl:choose>
        <xsl:when test="tei:list|tei:table|tei:p|tei:s|tei:w|tei:fw">
        <xsl:if test="normalize-space(translate(string(preceding-sibling::*[1]) ,'&#160;', ' '))">
        <gap class="label">
        <content><xsl:value-of select="string(preceding-sibling::*[1])" /></content>
        </gap>
        </xsl:if>
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



<xsl:template match="tei:lg" mode="structure">
    <xsl:text>
    </xsl:text>
    <xsl:choose>
    <xsl:when test="ancestor::tei:figDesc|ancestor::tei:item">
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

<xsl:template match="tei:epigraph" mode="structure">
    <div class="epigraph">
    <xsl:call-template name="textandorstructure" />
    </div>
</xsl:template>

<xsl:template match="tei:row" mode="structure">
    <row>
    <xsl:apply-templates mode="structure" />
    </row>
</xsl:template>

<xsl:template match="tei:div|tei:div0|tei:div1|tei:div2|tei:div3|tei:div4|tei:div5|tei:div6|tei:div7|tei:titlePage|tei:argument" mode="structure">
 <xsl:element name="div">
    <xsl:attribute name="class"><xsl:choose><xsl:when test="@type"><xsl:value-of select="@type" /></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute>
    <xsl:call-template name="metadata_link"/><!-- for INT collections? -->
    <xsl:apply-templates mode="structure" />
 </xsl:element>
</xsl:template>

<xsl:template match="tei:q|tei:quote" mode="structure">
    <xsl:choose>
      <xsl:when test="tei:list|tei:table">
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


<xsl:template match="tei:gap" mode="structure">
    <gap class="{@reason}">
        <xsl:if test="normalize-space(@resp) != ''">
            <xsl:attribute name="annotator"><xsl:value-of select="normalize-space(@resp)" /></xsl:attribute>
            <!-- MAYBE TODO: old style annotator may conflict with processors? -->
        </xsl:if>
    </gap>
</xsl:template>

<xsl:template match="tei:formula" mode="structure">
    <gap class="formula"><xsl:if test="normalize-space(.) != ''"><content><xsl:value-of select="." /></content></xsl:if></gap>
</xsl:template>

<xsl:template match="tei:interpGrp" mode="structure">
<xsl:if test="./tei:interp">w<comment>
<xsl:for-each select="./tei:interp">
    interp[<xsl:value-of select="@type"/>]: <xsl:value-of select="@value" />
</xsl:for-each>
</comment>
</xsl:if>
</xsl:template>

<!-- Valid both as structural and as markup, easy -->
<xsl:template match="tei:lb" mode="structure"><xsl:call-template name="lb" /></xsl:template>
<xsl:template match="tei:cb" mode="structure"><xsl:call-template name="cb" /></xsl:template>
<xsl:template match="tei:pb" mode="structure"><xsl:call-template name="pb" /></xsl:template>


<!-- Markup elements in structural mode, wrap in part (to be sorted by postprocessor later)-->


<!-- Text structural mode, wrap in part (to be sorted by postprocessor later!)-->
<xsl:template match="tei:l" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-l"><t><xsl:call-template name="l" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="tei:hi" mode="structure">
    <xsl:choose>
    <xsl:when test=".//tei:w[1]|.//tei:s[1]|.//tei:p[1]">
    <!-- styling is wrapped around structural elements, FoLiA requires the reverse -->
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">[tei2folia WARNING] styling wrapped around structural elements can not be converted yet (reduced to a comment)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] styling around structural element ignored: <xsl:value-of select="@rendition"/></comment>
    <!-- TODO: we could let the postprocessor pick this up and reapply it -->
    <xsl:call-template name="textandorstructure"/>
    </xsl:when>
    <xsl:when test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-hi" space="no"><t><xsl:call-template name="hi" /></t></part>
    </xsl:when>
    </xsl:choose>
</xsl:template>

<xsl:template match="tei:add" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-add" space="no"><t><xsl:call-template name="add" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="tei:corr" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-corr" space="no"><t><xsl:call-template name="corr" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="tei:supplied" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-supplied" space="no"><t><xsl:call-template name="supplied" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="tei:del" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-del" space="no"><t><xsl:call-template name="del" /></t></part>
    </xsl:if>
</xsl:template>

<xsl:template match="tei:note" mode="structure">
    <xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
    <part class="temp-note"><t><xsl:call-template name="note" /></t></part> <!-- this deliberately does not resolve to notes yet, our postprocessor creates the notes -->
    </xsl:if>
</xsl:template>

<xsl:template match="text()" mode="structure">
<xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
<part class="temp-text"><t><xsl:value-of select="." /></t></part>
</xsl:if>
</xsl:template>

<xsl:template match="tei:title" mode="structure">
<xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
<part class="temp-title"><t><xsl:call-template name="title" /></t></part>
</xsl:if>
</xsl:template>

<xsl:template match="tei:name" mode="structure">
<xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
<part class="temp-name"><t><xsl:call-template name="name" /></t></part>
</xsl:if>
</xsl:template>

<xsl:template match="tei:seg" mode="structure">
<xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
<part class="segment"><t><xsl:value-of select="." /></t></part>
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

<xsl:template match="tei:add" mode="markup">
<xsl:call-template name="add" />
</xsl:template>

<!-- styling (tei:hi) -->
<xsl:template name="hi">
<xsl:if test="normalize-space(string(.))">
<t-style><xsl:attribute name="class"><xsl:choose><xsl:when test="@rendition"><xsl:value-of select="@rendition"/></xsl:when><xsl:when test="@rend"><xsl:value-of select="@rend"/></xsl:when><xsl:otherwise>unspecified</xsl:otherwise></xsl:choose></xsl:attribute><xsl:apply-templates mode="markup"/></t-style>
</xsl:if>
</xsl:template>

<xsl:template match="tei:hi" mode="markup">
<xsl:call-template name="hi" />
</xsl:template>

<!-- more specific variants of styling -->
<xsl:template name="emph">
<xsl:if test="normalize-space(string(.))">
<t-style class="emphasis"><xsl:apply-templates mode="markup"/></t-style>
</xsl:if>
</xsl:template>

<xsl:template match="tei:emph" mode="markup">
<xsl:call-template name="emph" />
</xsl:template>

<xsl:template name="foreign">
<xsl:if test="normalize-space(string(.))">
<t-str class="foreign"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:foreign" mode="markup">
<xsl:call-template name="foreign" />
</xsl:template>

<xsl:template name="term">
<xsl:if test="normalize-space(string(.))">
<t-str class="term"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:term" mode="markup">
<xsl:call-template name="term" />
</xsl:template>

<xsl:template name="mentioned">
<xsl:if test="normalize-space(string(.))">
<t-str class="mentioned"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:mentioned" mode="markup">
<xsl:call-template name="mentioned" />
</xsl:template>

<xsl:template name="persName">
<xsl:if test="normalize-space(string(.))">
<t-str class="name-person"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:persName" mode="markup">
<xsl:call-template name="persName" />
</xsl:template>

<xsl:template name="placeName">
<xsl:if test="normalize-space(string(.))">
<t-str class="name-place"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:placeName" mode="markup">
<xsl:call-template name="placeName" />
</xsl:template>


<xsl:template name="geogName">
<xsl:if test="normalize-space(string(.))">
<t-str class="name-geography"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:geogName" mode="markup">
<xsl:call-template name="geogName" />
</xsl:template>

<xsl:template name="objectName">
<xsl:if test="normalize-space(string(.))">
<t-str class="name-object"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:objectName" mode="markup">
<xsl:call-template name="objectName" />
</xsl:template>

<xsl:template name="seg">
<xsl:if test="normalize-space(string(.))">
<t-str class="segment"><xsl:apply-templates mode="markup"/></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:seg" mode="markup">
<xsl:call-template name="seg" />
</xsl:template>

<!-- Valid both as structural and as markup, easy -->
<xsl:template name="lb"><br class="linebreak"/></xsl:template>
<xsl:template name="cb"><br class="columnbreak"/></xsl:template>
<xsl:template name="pb"><br class="pagebreak" newpage="yes"><xsl:if test="@n"><xsl:attribute name="pagenr"><xsl:value-of select="@n" /></xsl:attribute></xsl:if><xsl:call-template name="facs"/></br></xsl:template>

<xsl:template match="tei:lb" mode="markup"><xsl:call-template name="lb" /></xsl:template>
<xsl:template match="tei:cb" mode="markup"><xsl:call-template name="cb" /></xsl:template>
<xsl:template match="tei:pb" mode="markup"><xsl:call-template name="pb" /></xsl:template>

<xsl:template name="facs">
    <xsl:choose>
    <xsl:when test="substring(@facs,1,1) = '#'">
        <!-- refers to the original TEI (to a facsimile section usually) -->
        <relation class="facs" xlink:type="simple" format="application/tei+xml"><xsl:attribute name="xlink:href"><xsl:value-of select="$docid" />.tei.xml</xsl:attribute><xref><xsl:attribute name="id"><xsl:value-of select="@facs" /></xsl:attribute></xref></relation>
    </xsl:when>
    <xsl:when test="@facs">
        <!-- refers to an image directly (we hope) -->
        <relation class="facs" xlink:type="simple"><xsl:attribute name="xlink:href"><xsl:value-of select="@facs" /></xsl:attribute></relation>
    </xsl:when>
    </xsl:choose>
</xsl:template>

<!-- Converts an annotator with a link to a processor -->
<xsl:template name="resp2processor"><xsl:attribute name="processor"><xsl:choose><xsl:when test="@resp">proc.corrector.<xsl:value-of select="translate(@resp, ' :&#160;', '')"/></xsl:when><xsl:otherwise>proc.tei2folia.xsl</xsl:otherwise></xsl:choose></xsl:attribute></xsl:template>


<!-- Corrections -->
<!-- TODO: annotators should be in provenance chain, specifying them here probably fails even now -->
<xsl:template name="corr"><t-correction class="correction"><xsl:call-template name="resp2processor"/><xsl:if test="@sic"><xsl:attribute name="original"><xsl:value-of select="@sic" /></xsl:attribute></xsl:if><xsl:apply-templates mode="markup"/></t-correction></xsl:template>

<xsl:template name="supplied"><t-correction class="supplied"><xsl:call-template name="resp2processor"/><xsl:apply-templates mode="markup"/></t-correction></xsl:template>

<xsl:template name="del"><t-correction class="deletion" original="{.//text()}"><xsl:call-template name="resp2processor"/></t-correction></xsl:template>

<xsl:template match="tei:corr" mode="markup"><xsl:call-template name="corr" /></xsl:template>
<xsl:template match="tei:supplied" mode="markup"><xsl:call-template name="supplied" /></xsl:template>
<xsl:template match="tei:del" mode="markup"><xsl:call-template name="del" /></xsl:template>

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
        <xsl:otherwise><xsl:attribute name="class">unspecified</xsl:attribute></xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates mode="markup" /></t-ref>
</xsl:template>

<xsl:template match="tei:note" mode="markup"><xsl:call-template name="note" /></xsl:template>

<xsl:template name="quote">
    <xsl:if test="normalize-space(string(.))">
    <t-str class="quote"><xsl:apply-templates mode="markup" /></t-str>
    </xsl:if>
</xsl:template>
<xsl:template match="tei:q|tei:quote" mode="markup"><xsl:call-template name="quote" /></xsl:template>

<xsl:template name="gap">
    <t-gap class="{@reason}">
        <xsl:if test="normalize-space(@resp) != ''">
            <xsl:attribute name="annotator"><xsl:value-of select="normalize-space(@resp)" /></xsl:attribute>
            <!-- MAYBE TODO: old style annotator may conflict with processors? -->
        </xsl:if>
    </t-gap>
</xsl:template>
<xsl:template match="tei:gap" mode="markup"><xsl:call-template name="gap" /></xsl:template>

<!--
<xsl:template match="tei:formula" mode="markup">
    <t-gap class="formula"><xsl:value-of select="." /></t-gap>
</xsl:template>
-->

<xsl:template match="tei:note[./tei:table|./tei:figure|./tei:list|./tei:p]" mode="markup">
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

<xsl:template match="tei:l" mode="markup">
<xsl:call-template name="l" />
</xsl:template>

<!-- default text node behaviour -->
<xsl:template match="text()" mode="markup">
<xsl:value-of select="." />
</xsl:template>

<xsl:template name="title">
<xsl:if test="normalize-space(translate(string(.),'&#160;', ' '))">
<t-str class="title"><xsl:apply-templates mode="markup" /></t-str>
</xsl:if>
</xsl:template>

<xsl:template match="tei:title" mode="markup">
<xsl:call-template name="title" />
</xsl:template>

<!-- ************************** TEMPLATES DELETING ELEMENTS  *********************** -->

<!-- Deletion often occurs because the element is already handled elsewhere -->

<!-- I suppose this cleans up something from some preprocessing step? leaving it in just in case -->
<xsl:template match="tei:supplied[./text()='leeg']" mode="markup"/>
<xsl:template match="tei:supplied[./text()='leeg']" mode="structure"/>

<!-- Handled by item -->
<xsl:template match="tei:label" mode="structure"/>

<!-- Handled by table -->
<xsl:template match="tei:table/tei:head" mode="structure"/>

<!-- Handled by list -->
<xsl:template match="tei:list/tei:head" mode="structure"/>

<!-- Handled by figure -->
<xsl:template match="tei:figure/tei:head" mode="structure"/>

<!-- *********************************** PAGEBREAK MAGIC **************************************************** -->

<xsl:template match="tei:text/tei:pb|tei:table/tei:pb|tei:row/tei:pb|tei:list/tei:pb" mode="structure"><comment>[tei2folia WARNING] Skipping pagebreak here</comment></xsl:template>
<xsl:template match="tei:list/tei:lb|tei:row/tei:lb|tei:table/tei:lb" mode="structure"><comment>[tei2folia WARNING] Skipping linebreak here</comment></xsl:template>
<xsl:template match="tei:text/tei:pb|tei:table/tei:pb|tei:row/tei:pb|tei:list/tei:pb" mode="markup"><comment>[tei2folia WARNING] Skipping pagebreak here</comment></xsl:template>
<xsl:template match="tei:list/tei:lb|tei:row/tei:lb|tei:table/tei:lb" mode="markup"><comment>[tei2folia WARNING] Skipping linebreak here</comment></xsl:template>

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
<xsl:if test="self::tei:pb and (not(ancestor::tei:div)) and (not(ancestor::tei:div1))  and (not(ancestor::tei:titlePage))">
<comment>opgeviste pagebreak:</comment>
<xsl:call-template name="pb"/>
</xsl:if>
</xsl:for-each>
</xsl:template>



<xsl:template name="haalPbBinnenInCel">
<xsl:for-each select="..">
<xsl:for-each select="preceding-sibling::*[1]">
<xsl:if test="self::tei:pb">
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




<xsl:template match="tei:delSpan">
<xsl:variable name="spanTo"><xsl:value-of select="@spanTo"/></xsl:variable>
<xsl:variable name="end"><xsl:value-of select="following-sibling::anchor[@xml:id=$spanTo]"/></xsl:variable>
<xsl:if test="$end">
<xsl:message>Deleted text: (<xsl:value-of select="name($end)"/>) <xsl:value-of select="$end/preceding-sibling::node()[preceding-sibling::delSpan[@spanTo=$spanTo]]"/>
</xsl:message>
</xsl:if>
</xsl:template>


<xsl:template match="tei:sp" mode="structure">
    <xsl:choose>
    <xsl:when test="ancestor::tei:figDesc|ancestor::tei:item|ancestor::tei:quote|ancestor::tei:q">
        <!-- no events allowed under these elements, just descend into substructures -->
        <xsl:apply-templates mode="structure" />
    </xsl:when>
    <xsl:otherwise>
        <!-- normal behaviour -->
        <event class="speakerturn">
        <xsl:choose>
        <xsl:when test=".//tei:speaker/tei:hi">
            <xsl:attribute name="actor"><xsl:value-of select="string(.//tei:speaker/tei:hi)" /></xsl:attribute>
        </xsl:when>
        <xsl:when test=".//tei:speaker">
            <xsl:attribute name="actor"><xsl:value-of select="string(.//tei:speaker)" /></xsl:attribute>
        </xsl:when>
        </xsl:choose>
        <xsl:call-template name="textandorstructure" />
        </event>
    </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template match="tei:stage" mode="structure">
<event class="stage">
    <xsl:call-template name="textandorstructure"/>
</event>
</xsl:template>



<xsl:template match="tei:add[@resp='transcriber']"/>



<!-- ********************************** WARNINGS ***************************************************** -->

<xsl:template match="tei:item/tei:figure" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in item! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in item! (not allowed)</comment>
</xsl:template>

<xsl:template match="tei:quote/tei:figure|tei:q/tei:figure" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in quote! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in quote! (not allowed)</comment>
</xsl:template>

<xsl:template match="tei:figDesc/tei:figure|tei:figDesc/tei:list|tei:figDesc/tei:table" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: skipping <xsl:value-of select="name()" /> in caption! (not allowed)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] skipping <xsl:value-of select="name()" /> in caption! (not allowed)</comment>
</xsl:template>


<!-- generic fallbacks -->

<xsl:template match="*" mode="structure">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag in structure context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />); text: <xsl:value-of select="."/></xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Unhandled tag in structure context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</comment>
</xsl:template>

<xsl:template match="*" mode="markup">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag in markup context: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />); text: <xsl:value-of select="."/></xsl:message>
    </xsl:if>
    <xsl:value-of select="string(.)"/>
</xsl:template>

<xsl:template match="*">
    <xsl:if test="$quiet = 'false'">
    <xsl:message terminate="no">WARNING: Unknown tag: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</xsl:message>
    </xsl:if>
    <comment>[tei2folia WARNING] Unhandled tag: <xsl:value-of select="name(.)"/> (in <xsl:value-of select="name(parent::node())" />)</comment>
</xsl:template>


</xsl:stylesheet>
